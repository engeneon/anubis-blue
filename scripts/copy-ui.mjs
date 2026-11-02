import { copyFileSync, mkdirSync } from "node:fs";
mkdirSync("ui/dist", { recursive: true });
for (const file of ["index.html", "style.css"])
  copyFileSync("ui/src/" + file, "ui/dist/" + file);

copyFileSync("docs/usability-user-guide.html", "ui/dist/user-guide.html");

copyFileSync("ui/assets/anubis-logo.png", "ui/dist/anubis-logo.png");

copyFileSync("docs/copilot-operation.txt", "ui/dist/copilot-guide.txt");
