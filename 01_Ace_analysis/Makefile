
all: build sim rw-parse

build: 
	fusesoc --cores-root=.. run --target=sim --setup --build lowrisc:ibex:ibex_simple_system --RV32M=1 --RV32E=0

sim:
	../build/lowrisc_ibex_ibex_simple_system_0/sim-verilator/Vibex_simple_system -t --raminit=../examples/sw/simple_system/hello_test/hello_test.vmem

rw-parse:
	python ibex_add_fwrite.py -c

find-dep:
	cd .. && python ./01_Ace_analysis/print_design_list.py ./ibex_top_tracing.core && cd 01_Ace_analysis/
	mv ../sv_list .

modify-rtl:
	cd .. && ./01_Ace_analysis/.ACE_modify_design && cd 01_Ace_analysis/

recover-rtl:
	cd ..  && ./01_Ace_analysis/.ACE_recover_design && cd 01_Ace_analysis/

clean:
	rm -rf ./build
	rm -f *.vcd
	rm -f trace_core_00000000.log
	rm -f ibex_simple_system.log
	rm -f ibex_simple_system_pcount.csv
