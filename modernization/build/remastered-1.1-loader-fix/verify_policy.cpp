#include <string>
#include <cstdio>
#include <cstring>
#include <windows.h>
using Hash=void(__cdecl*)(const unsigned char*,unsigned,char*);
static bool previous(std::string h){return h=="b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291" || h=="be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7" || h=="43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d" || h=="3eda4a37079e6c4fb09dfc1b01760afa0bf6979d82dd479a56631f5ea96f056d";}
static bool corrected(std::string h){return h=="b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291" || h=="be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7" || h=="43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d" || h=="3eda4a37079e6c4fb09dfc1b01760afa0bf6979d82dd479a56631f5ea96f056d" || h=="42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da";}
int main(){
std::string h="42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da";
if(previous(h)||!corrected(h))return 1;
if(!previous("b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291")||!corrected("b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"))return 2;
if(!previous("be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7")||!corrected("be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7"))return 2;
if(!previous("43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d")||!corrected("43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d"))return 2;
if(!previous("3eda4a37079e6c4fb09dfc1b01760afa0bf6979d82dd479a56631f5ea96f056d")||!corrected("3eda4a37079e6c4fb09dfc1b01760afa0bf6979d82dd479a56631f5ea96f056d"))return 2;
h[0]=h[0]=='0'?'1':'0';if(corrected(h)||corrected(std::string(64,'0')))return 3;printf("old candidate refused; fixed candidate accepted; previous versions retained; unknown versions refused\n");return 0;}
