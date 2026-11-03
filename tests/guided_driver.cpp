#include "application/characterization/guided.hpp"
#include <fstream>
#include <iostream>
using namespace anubis;
int main(int argc,char**argv){try {require((argc==3||argc==4),"args","root input");Json b,p;std::ifstream(argv[2])>>b;std::ifstream(std::string(argv[1])+"/knowledge/guided-intake.json")>>p;std::cout<<(argc==4?gpu_readiness(b):guided_workload(b,p)).dump(2);return 0;}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
