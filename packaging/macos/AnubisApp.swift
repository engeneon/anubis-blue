// Anubis.app: a native window around the local Anubis service.
// It starts the bundled server, signs in automatically and shows the UI.
import Cocoa
import WebKit

let appName = "Anubis"

final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate,
  WKDownloadDelegate, WKScriptMessageHandler
{
  var window: NSWindow!
  var webView: WKWebView!
  var server: Process?
  var port = 8787
  var token = ""
  var quitting = false
  var downloadTargets: [ObjectIdentifier: URL] = [:]

  let fm = FileManager.default
  lazy var dataDir: URL = {
    let base = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
    return base.appendingPathComponent(appName, isDirectory: true)
  }()
  lazy var logDir: URL = {
    fm.urls(for: .libraryDirectory, in: .userDomainMask)[0]
      .appendingPathComponent("Logs/\(appName)", isDirectory: true)
  }()
  var logFile: URL { logDir.appendingPathComponent("server.log") }

  // MARK: Launch

  func applicationDidFinishLaunching(_ note: Notification) {
    buildMenu()
    buildWindow()
    do {
      try prepareData()
      try startServer()
    } catch {
      fail("Anubis could not start.", detail: error.localizedDescription)
      return
    }
    waitForServer(deadline: Date().addingTimeInterval(30))
  }

  func applicationShouldTerminateAfterLastWindowClosed(_ app: NSApplication) -> Bool { true }

  func applicationWillTerminate(_ note: Notification) {
    quitting = true
    guard let s = server, s.isRunning else { return }
    s.terminate()
    let deadline = Date().addingTimeInterval(5)
    while s.isRunning && Date() < deadline { usleep(50_000) }
    if s.isRunning { kill(s.processIdentifier, SIGKILL) }
  }

  /// Creates the private data folder and, on first launch, the local-owner identity.
  func prepareData() throws {
    umask(0o077)
    try fm.createDirectory(at: dataDir, withIntermediateDirectories: true,
                           attributes: [.posixPermissions: 0o700])
    try fm.createDirectory(at: logDir, withIntermediateDirectories: true)
    let identity = dataDir.appendingPathComponent("identities.json")
    if !fm.fileExists(atPath: identity.path) {
      var bytes = [UInt8](repeating: 0, count: 32)
      guard SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes) == errSecSuccess else {
        throw NSError(domain: appName, code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "Could not create an access token."])
      }
      let t = Data(bytes).base64EncodedString()
        .replacingOccurrences(of: "+", with: "-").replacingOccurrences(of: "/", with: "_")
        .replacingOccurrences(of: "=", with: "")
      let json = [["id": "local-owner", "role": "admin", "token": t]]
      let data = try JSONSerialization.data(withJSONObject: json, options: [.prettyPrinted, .sortedKeys])
      try data.write(to: identity, options: .atomic)
      try fm.setAttributes([.posixPermissions: 0o600], ofItemAtPath: identity.path)
    }
    let parsed = try JSONSerialization.jsonObject(with: Data(contentsOf: identity)) as? [[String: Any]]
    guard let owner = parsed?.first(where: { $0["id"] as? String == "local-owner" }) ?? parsed?.first,
          let t = owner["token"] as? String
    else {
      throw NSError(domain: appName, code: 2,
                    userInfo: [NSLocalizedDescriptionKey: "identities.json has no usable token."])
    }
    token = t
  }

  /// Provider keys from the optional private .env file, same rules as deploy/local/run.py.
  func providerEnvironment() -> [String: String] {
    let aliases = ["OPENAI_API_KEY": "ANUBIS_AI_KEY_OPENAI", "ANTHROPIC_API_KEY": "ANUBIS_AI_KEY_ANTHROPIC",
                   "DEEPSEEK_API_KEY": "ANUBIS_AI_KEY_DEEPSEEK", "XAI_API_KEY": "ANUBIS_AI_KEY_XAI"]
    var env: [String: String] = [:]
    guard let text = try? String(contentsOf: dataDir.appendingPathComponent(".env"), encoding: .utf8)
    else { return env }
    for raw in text.split(whereSeparator: \.isNewline) {
      var line = raw.trimmingCharacters(in: .whitespaces)
      if line.hasPrefix("export ") { line = String(line.dropFirst(7)) }
      guard !line.hasPrefix("#"), let eq = line.firstIndex(of: "=") else { continue }
      let name = line[..<eq].trimmingCharacters(in: .whitespaces)
      let value = line[line.index(after: eq)...].trimmingCharacters(in: .whitespaces)
        .trimmingCharacters(in: CharacterSet(charactersIn: "\"'"))
      if let alias = aliases[name] { env[alias] = env[alias] ?? value }
      else if name.hasPrefix("ANUBIS_AI_KEY_") { env[name] = env[name] ?? value }
    }
    return env
  }

  func portIsFree(_ p: Int) -> Bool {
    let fd = socket(AF_INET, SOCK_STREAM, 0)
    guard fd >= 0 else { return false }
    defer { close(fd) }
    var addr = sockaddr_in()
    addr.sin_family = sa_family_t(AF_INET)
    addr.sin_port = in_port_t(UInt16(p).bigEndian)
    addr.sin_addr.s_addr = inet_addr("127.0.0.1")
    return withUnsafePointer(to: &addr) {
      $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
        Darwin.bind(fd, $0, socklen_t(MemoryLayout<sockaddr_in>.size)) == 0
      }
    }
  }

  func startServer() throws {
    guard let p = (8787...8887).first(where: portIsFree) else {
      throw NSError(domain: appName, code: 3,
                    userInfo: [NSLocalizedDescriptionKey: "No free local port between 8787 and 8887."])
    }
    port = p
    let bundle = Bundle.main
    let binary = bundle.bundleURL.appendingPathComponent("Contents/MacOS/anubis-server")
    let root = bundle.resourceURL!.appendingPathComponent("anubis", isDirectory: true)
    let proc = Process()
    proc.executableURL = binary
    proc.arguments = ["--root", root.path, "--db", dataDir.appendingPathComponent("anubis.sqlite").path,
                      "--port", String(port)]
    var env = ProcessInfo.processInfo.environment
    env["ANUBIS_IDENTITIES"] = dataDir.appendingPathComponent("identities.json").path
    let neon = dataDir.appendingPathComponent("neon-target.json")
    if fm.fileExists(atPath: neon.path) && env["ANUBIS_NEON_TARGET"] == nil { env["ANUBIS_NEON_TARGET"] = neon.path }
    for (k, v) in providerEnvironment() where env[k] == nil { env[k] = v }
    proc.environment = env
    proc.currentDirectoryURL = dataDir
    if !fm.fileExists(atPath: logFile.path) { fm.createFile(atPath: logFile.path, contents: nil) }
    let log = try FileHandle(forWritingTo: logFile)
    log.seekToEndOfFile()
    log.write("\n--- \(Date()) Anubis \(version) on port \(port)\n".data(using: .utf8)!)
    proc.standardOutput = log
    proc.standardError = log
    proc.terminationHandler = { [weak self] p in
      DispatchQueue.main.async {
        guard let self, !self.quitting else { return }
        self.fail("The Anubis service stopped (exit \(p.terminationStatus)).", detail: self.logTail())
      }
    }
    try proc.run()
    server = proc
  }

  var version: String {
    Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "?"
  }
  var baseURL: URL { URL(string: "http://127.0.0.1:\(port)/")! }

  func waitForServer(deadline: Date) {
    var req = URLRequest(url: baseURL, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 1)
    req.httpMethod = "GET"
    URLSession.shared.dataTask(with: req) { [weak self] _, resp, _ in
      DispatchQueue.main.async {
        guard let self, !self.quitting else { return }
        if resp is HTTPURLResponse { self.openUI(); return }
        if self.server?.isRunning != true { return }  // terminationHandler reports it
        if Date() > deadline {
          self.fail("Anubis did not start within 30 seconds.", detail: self.logTail())
          return
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) { self.waitForServer(deadline: deadline) }
      }
    }.resume()
  }

  /// Sets the session cookie the server expects, then loads the UI already signed in.
  func openUI() {
    let cookie = HTTPCookie(properties: [
      .name: "anubis_session", .value: token, .domain: "127.0.0.1", .path: "/",
      HTTPCookiePropertyKey("HttpOnly"): "TRUE", .sameSitePolicy: HTTPCookieStringPolicy.sameSiteStrict,
    ])!
    webView.configuration.websiteDataStore.httpCookieStore.setCookie(cookie) { [weak self] in
      guard let self else { return }
      self.webView.load(URLRequest(url: self.baseURL))
    }
  }

  func logTail() -> String {
    guard let text = try? String(contentsOf: logFile, encoding: .utf8) else { return "" }
    return text.split(separator: "\n").suffix(12).joined(separator: "\n")
  }

  func fail(_ message: String, detail: String) {
    let alert = NSAlert()
    alert.messageText = message
    alert.informativeText = detail.isEmpty ? "See \(logFile.path)" : detail + "\n\nLog: \(logFile.path)"
    alert.alertStyle = .critical
    alert.addButton(withTitle: "Quit")
    alert.addButton(withTitle: "Show Log")
    if alert.runModal() == .alertSecondButtonReturn { NSWorkspace.shared.activateFileViewerSelecting([logFile]) }
    NSApp.terminate(nil)
  }

  // MARK: Window and menu

  func buildWindow() {
    let config = WKWebViewConfiguration()
    config.websiteDataStore = .default()
    // window.print() is a no-op in WKWebView; route it to a native print panel.
    let printShim = WKUserScript(
      source: "window.print = function(){ window.webkit.messageHandlers.anubisPrint.postMessage(null); };",
      injectionTime: .atDocumentStart, forMainFrameOnly: true)
    config.userContentController.addUserScript(printShim)
    config.userContentController.add(self, name: "anubisPrint")
    webView = WKWebView(frame: .zero, configuration: config)
    webView.navigationDelegate = self
    webView.uiDelegate = self
    webView.allowsMagnification = true
    window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1360, height: 900),
                      styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
    window.title = appName
    window.contentView = webView
    window.setFrameAutosaveName("AnubisMain")
    window.center()
    window.makeKeyAndOrderFront(nil)
    NSApp.activate(ignoringOtherApps: true)
    webView.loadHTMLString(
      "<html><body style='font:15px -apple-system;color:#888;display:flex;align-items:center;justify-content:center;height:90vh'>Starting Anubis…</body></html>",
      baseURL: nil)
  }

  func buildMenu() {
    let main = NSMenu()
    func add(_ title: String, _ build: (NSMenu) -> Void) {
      let item = NSMenuItem(); let menu = NSMenu(title: title); build(menu); item.submenu = menu; main.addItem(item)
    }
    add(appName) { m in
      m.addItem(withTitle: "About \(appName)", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
      m.addItem(.separator())
      m.addItem(withTitle: "Copy Access Token", action: #selector(copyToken), keyEquivalent: "")
      m.addItem(withTitle: "Show Data Folder", action: #selector(showData), keyEquivalent: "")
      m.addItem(withTitle: "Show Server Log", action: #selector(showLog), keyEquivalent: "")
      m.addItem(withTitle: "Open in Browser", action: #selector(openInBrowser), keyEquivalent: "")
      m.addItem(.separator())
      m.addItem(withTitle: "Hide \(appName)", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
      m.addItem(withTitle: "Quit \(appName)", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
    }
    add("Edit") { m in
      m.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
      m.addItem(withTitle: "Redo", action: Selector(("redo:")), keyEquivalent: "Z")
      m.addItem(.separator())
      m.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
      m.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
      m.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
      m.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
    }
    add("View") { m in
      m.addItem(withTitle: "Reload", action: #selector(reload), keyEquivalent: "r")
      m.addItem(withTitle: "Back", action: #selector(goBack), keyEquivalent: "[")
      m.addItem(withTitle: "Actual Size", action: #selector(zoomReset), keyEquivalent: "0")
      m.addItem(withTitle: "Zoom In", action: #selector(zoomIn), keyEquivalent: "+")
      m.addItem(withTitle: "Zoom Out", action: #selector(zoomOut), keyEquivalent: "-")
    }
    add("Window") { m in
      m.addItem(withTitle: "Minimize", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
      m.addItem(withTitle: "Close", action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
      NSApp.windowsMenu = m
    }
    NSApp.mainMenu = main
  }

  @objc func copyToken() {
    NSPasteboard.general.clearContents()
    NSPasteboard.general.setString(token, forType: .string)
  }
  @objc func showData() { NSWorkspace.shared.open(dataDir) }
  @objc func showLog() { NSWorkspace.shared.activateFileViewerSelecting([logFile]) }
  @objc func openInBrowser() { NSWorkspace.shared.open(baseURL) }
  @objc func reload() { webView.reload() }
  @objc func goBack() { webView.goBack() }
  @objc func zoomReset() { webView.pageZoom = 1 }
  @objc func zoomIn() { webView.pageZoom = min(webView.pageZoom + 0.1, 3) }
  @objc func zoomOut() { webView.pageZoom = max(webView.pageZoom - 0.1, 0.5) }

  // MARK: Web view behaviour

  func isLocal(_ url: URL?) -> Bool {
    guard let url else { return false }
    return url.scheme == "about" || url.scheme == "blob" || url.scheme == "data"
      || (url.host == "127.0.0.1" && url.port == port)
  }

  func webView(_ wv: WKWebView, decidePolicyFor action: WKNavigationAction,
               decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
    if action.shouldPerformDownload { decisionHandler(.download); return }
    if let url = action.request.url, !isLocal(url), action.navigationType == .linkActivated {
      NSWorkspace.shared.open(url); decisionHandler(.cancel); return
    }
    decisionHandler(.allow)
  }

  func webView(_ wv: WKWebView, decidePolicyFor response: WKNavigationResponse,
               decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
    decisionHandler(response.canShowMIMEType ? .allow : .download)
  }

  func webView(_ wv: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) {
    download.delegate = self
  }
  func webView(_ wv: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) {
    download.delegate = self
  }

  // target=_blank: local pages open in this window, anything else in the default browser.
  func webView(_ wv: WKWebView, createWebViewWith config: WKWebViewConfiguration,
               for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
    if let url = action.request.url {
      if isLocal(url) { wv.load(action.request) } else { NSWorkspace.shared.open(url) }
    }
    return nil
  }

  func download(_ download: WKDownload, decideDestinationUsing response: URLResponse,
                suggestedFilename: String, completionHandler: @escaping (URL?) -> Void) {
    let panel = NSSavePanel()
    panel.nameFieldStringValue = suggestedFilename
    panel.directoryURL = fm.urls(for: .downloadsDirectory, in: .userDomainMask).first
    panel.beginSheetModal(for: window) { [weak self] result in
      guard result == .OK, let url = panel.url else { completionHandler(nil); return }
      try? self?.fm.removeItem(at: url)  // the save panel already confirmed replacing
      completionHandler(url)
    }
  }

  func download(_ download: WKDownload, didFailWithError error: Error, resumeData: Data?) {
    let a = NSAlert(); a.messageText = "Download failed"; a.informativeText = error.localizedDescription
    a.beginSheetModal(for: window)
  }

  func webView(_ wv: WKWebView, runOpenPanelWith params: WKOpenPanelParameters,
               initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
    let panel = NSOpenPanel()
    panel.allowsMultipleSelection = params.allowsMultipleSelection
    panel.canChooseDirectories = params.allowsDirectories
    panel.canChooseFiles = true
    panel.beginSheetModal(for: window) { completionHandler($0 == .OK ? panel.urls : nil) }
  }

  func webView(_ wv: WKWebView, runJavaScriptAlertPanelWithMessage message: String,
               initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
    let a = NSAlert(); a.messageText = message; a.addButton(withTitle: "OK")
    a.beginSheetModal(for: window) { _ in completionHandler() }
  }

  func webView(_ wv: WKWebView, runJavaScriptConfirmPanelWithMessage message: String,
               initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
    let a = NSAlert(); a.messageText = message; a.addButton(withTitle: "OK"); a.addButton(withTitle: "Cancel")
    a.beginSheetModal(for: window) { completionHandler($0 == .alertFirstButtonReturn) }
  }

  func webView(_ wv: WKWebView, runJavaScriptTextInputPanelWithPrompt prompt: String, defaultText: String?,
               initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (String?) -> Void) {
    let a = NSAlert(); a.messageText = prompt; a.addButton(withTitle: "OK"); a.addButton(withTitle: "Cancel")
    let field = NSTextField(frame: NSRect(x: 0, y: 0, width: 320, height: 24))
    field.stringValue = defaultText ?? ""
    a.accessoryView = field
    a.window.initialFirstResponder = field
    a.beginSheetModal(for: window) { completionHandler($0 == .alertFirstButtonReturn ? field.stringValue : nil) }
  }

  func userContentController(_ ucc: WKUserContentController, didReceive message: WKScriptMessage) {
    guard message.name == "anubisPrint" else { return }
    let info = NSPrintInfo.shared
    info.horizontalPagination = .fit
    info.verticalPagination = .automatic
    let op = webView.printOperation(with: info)
    op.view?.frame = webView.bounds
    op.runModal(for: window, delegate: nil, didRun: nil, contextInfo: nil)
  }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
