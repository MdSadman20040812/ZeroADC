mach create "cdm_zeroadc"
machine LoadPlatformDescription @platforms/cpus/stm32l552.repl
sysbus LoadELF "D:\Outputs\PaperFix\renode\app_cdm.elf"
start
sleep 3
echo "--- MARKERS ---"
sysbus ReadWord 0x20000040
sysbus ReadWord 0x20000044
sysbus ReadWord 0x20000048
sysbus ReadWord 0x2000004C
sysbus ReadWord 0x20000050
sysbus ReadWord 0x20000054
sysbus ReadWord 0x20000058
sysbus ReadWord 0x2000005C
sysbus ReadWord 0x20000060
echo "--- EMULATION DONE ---"
quit
