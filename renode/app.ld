MEMORY
{
  FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 512K
  RAM (xrw)  : ORIGIN = 0x20000000, LENGTH = 192K
}
ENTRY(Reset_Handler)
SECTIONS
{
  .isr_vector : { KEEP(*(.isr_vector)) } > FLASH
  .text : { *(.text*) *(.rodata*) _etext = .; } > FLASH
  .data : { *(.data*) _edata = .; } > RAM AT > FLASH
  .bss : { *(.bss*) *(COMMON) _ebss = .; } > RAM
}
