#include "application/characterization/resolve.hpp"
#include "compiler/compiler.hpp"
#include <fstream>
#include <iostream>
using namespace anubis;
Json read(const std::string &p){std::ifstream f(p);Json j;f>>j;return j;}
int main(int argc,char**argv){try{require(argc==2,"test","Root required");std::string root=argv[1];auto cat=read(root+"/knowledge/architecture-core.json"),cases=read(root+"/tests/fixtures/architecture-boundary-scenarios.json");int n=0;
for(const auto&s:cases){auto r=characterize(s["answers"],cat);require(r["patterns"]==s["expected_patterns"],"match",s["id"].get<std::string>());require(r==characterize(s["answers"],cat),"determinism","Repeat differs");validate_workload(r["workload"]);for(const auto &a:r["workload"]["stages"])require(a["type"]=="unsupported","scope","Discovery must not claim quantitative support");if(s["expected_question"].is_string()){bool found=false;for(const auto&q:r["questions"])if(q.get<std::string>().find(s["expected_question"].get<std::string>())!=std::string::npos)found=true;require(found,"question",s["id"].get<std::string>());}++n;}
auto a=cases[8]["answers"];auto r=characterize(a,cat);require(r["workload"]["scenarios"].size()==2,"schedule","Non-overlap lost");
for(int i=0;i<4;++i){auto bad=cases[9]["answers"];if(i==0)bad["overlap"]="no";if(i==1)bad["activities"][1]["predecessor"]=1;if(i==2)bad["activities"][0]["answers"]["stream"]="maybe";if(i==3)bad["activities"][0]["location"]="moon";bool rejected=false;try{characterize(bad,cat);}catch(const Error&){rejected=true;}require(rejected,"negative","Invalid answers accepted");}
std::cout<<n<<" scenario expectations + repeatability + draft validation + 4 negative checks passed\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
