import re
import pandas as pd
import argparse
from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import *
from collections import OrderedDict

def rw_parse():
    print("========================rw_parse start===================================")
    logs = ["./sim_logs/ibex_alu_log.txt",
            "./sim_logs/ibex_compressed_decoder_log.txt",
            "./sim_logs/ibex_controller_log.txt",
            "./sim_logs/ibex_core_log.txt",
            "./sim_logs/ibex_counter_log.txt",
            "./sim_logs/ibex_cs_registers_log.txt",
            "./sim_logs/ibex_csr_log.txt",
            "./sim_logs/ibex_decoder_log.txt",
            "./sim_logs/ibex_ex_block_log.txt",
            "./sim_logs/ibex_fetch_fifo_log.txt",
            "./sim_logs/ibex_id_stage_log.txt",
            "./sim_logs/ibex_if_stage_log.txt",
            "./sim_logs/ibex_load_store_unit_log.txt",
            "./sim_logs/ibex_multdiv_slow_log.txt",
            "./sim_logs/ibex_prefetch_buffer_log.txt",
            "./sim_logs/ibex_register_file_ff_log.txt",
            "./sim_logs/ibex_top_log.txt",
            #"./sim_logs/ibex_top_tracing_log.txt",
            "./sim_logs/ibex_tracer_log.txt",
            "./sim_logs/ibex_wb_stage_log.txt"]
    rw_table = {}

    for i in logs:
        with open (i,"r") as reader:
            lines = reader.readlines()
            for line in lines[:-1]:
                line = line.strip()
                sim_time = int(line.split("cycle :")[0].strip())
                rw_info = line.split("cycle :")[1].strip()
                if sim_time in rw_table.keys():
                    rw_table[sim_time].append(rw_info)
                else:
                    rw_table[sim_time]=[]

    ordered_dict = OrderedDict(sorted(rw_table.items()))
    
    with open("assign_log.csv","w") as writer:
        writer.write("sim_time,assign\n")
        for key, content in ordered_dict.items():
            writer.write(str(key)+",\""+str(content)+"\"\n")

def sv_rewrite_format(old_file,new_file):

    print("=================================== rewrite_format start ==================================")
    filename = new_file.rsplit("/",1)[1].split(".")[0]
    with open(old_file, "r") as f:
        content = f.read()

    # Remove comments
    new_content = re.sub(r"\/\/[^\n]*\n", "", content)
    new_content = re.sub(r"\/\*[\w\W]+?\*\/","",new_content)

    new_content = re.sub(r"\sreg\s*\[", "\nreg [", new_content)
    new_content = re.sub(r"\swire\s*\[", "\nwire [", new_content)
    new_content = re.sub(r"\bend\b", "\nend", new_content)
    new_content = re.sub(r"\bbegin\b(?!\s*:)", "begin\n", new_content)
    new_content = re.sub(r";", ";\n", new_content)
    regex = re.compile(r"\bfor\s*\(([^;]*);\n([^;]*);\n([^;\)]*)\)")
    new_content = re.sub(regex, r'for (\1;\2;\3)', new_content)
    new_content = re.sub(r"[ ]*\n", "\n", new_content)
    new_content = re.sub(r"\n[ ]*", "\n", new_content)
    new_content = re.sub(r"[ ]+", " ", new_content)
    new_content = re.sub(r"\n+", "\n", new_content)
    new_content = re.sub(r"\n\\\n", "\\\n", new_content)
    new_content = re.sub(r"(?<=[^\s=><\^|\+\!])\s*=\s*(?!=)", " = ", new_content)

    # Make the codes of begin with assign in one line.
    assign_blocks = re.findall(r"\bassign [^;]+?;", new_content)
    for block in assign_blocks:
        b = block.replace("\n","")
        new_content = new_content.replace(block, b)

    # Make the varible assignments in one line.
    if re.search(r"\bmodule\b[^;]+?;", new_content):
        module_block = re.findall(r"\bmodule\b[^;]+?;", new_content)[0]
        module_block_tail = new_content.split(module_block)[1]
        module_block = new_content.split(module_block)[0]+module_block
        eq_blocks = re.findall(r"(?<!parameter\b)[^=;\n]+\s*=\s*[^=;]+?;", module_block_tail)
        for block in eq_blocks:
            b = block.replace("\n"," ")
            module_block_tail = module_block_tail.replace(block, b)
        new_content = module_block + module_block_tail
        eq_blocks = re.findall(r" = [^;]+?;", module_block_tail)
        for block in eq_blocks:
            b = block.replace("\n"," ")
            new_content = new_content.replace(block, b)

    # Make the localparam setting codes in one line.
    localparam_blocks = re.findall(r"\blocalparam [^;]+?;", new_content)
    for block in localparam_blocks:
        b = block.replace("\n","")
        new_content = new_content.replace(block, b)

    # Put file open code into the RTL file.
    moduleblock = re.findall(r"\bmodule [\w\W]+?\)\s*;", new_content)
    for block in moduleblock:
        b = block + "\ninteger f;\ninitial begin\nf = $fopen(\"./01_Ace_analysis/sim_logs/{}_log.txt\", \"w\");\nend\n".format(filename)
        new_content = new_content.replace(block, b)

    with open(new_file, "w") as f:
        f.write(new_content)
    
    print("=================================== rewrite_format done ===================================")

def add_display(old_file,new_file):
    print("=================================== add_display start =====================================")
    content = []
    with open(old_file, "r") as r:
        reader = r.readlines()
    line_count = 0
    module_flag = 0
    beginend_flag = 0
    for line in reader:

        if ("module " in line) and (module_flag == 0):
            module_flag = 1
        elif ("endmodule" in line) and (module_flag == 1):
            module_flag = 0
        
        if module_flag == 1:
            line = line.strip()
            if  (line.find("=")) != -1 and line.find("para") == -1 and \
                line.find("wire") == -1 and line.find("assign") == -1 and \
                line.find("for") == -1 and line.find("fopen(") == -1 and \
                line.find("logic") == -1 and (beginend_flag > 0) :
                if line.find("if") != -1:
                    """ line_count += 1
                    content = content + [("$fwrite(f,\"%0t cycle :{}:{}\\n\"  , $time);\n").format(new_file,line_count)] """
                    content = content + [("{}\n").format(line)]
                    line_count += 1
                elif line.find("case") != -1 and line.find("(") != -1:
                    """ line_count += 1
                    content = content + [("$fwrite(f,\"%0t cycle :{}:{}\\n\"  , $time);\n").format(new_file,line_count)] """
                    content = content + [("{}\n").format(line)]
                    line_count += 1
                else:
                    content = content + [("{}\n").format(line)]
                    line_count += 1
                    content = content + [("$fwrite(f,\"%0t cycle :{}:{}\\n\"  , $time);\n").format(new_file,line_count)]
                    line_count += 1
            else:
                if line.find("if") != -1 and line.find("(") != -1 and (beginend_flag > 0):
                    """ line_count += 1
                    content = content + [("$fwrite(f,\"%0t cycle :{}:{}\\n\"  , $time);\n").format(new_file,line_count+1)] """
                    content = content + [("{}\n").format(line)]
                    line_count += 1
                elif line.find("case") != -1 and line.find("(") != -1 and (beginend_flag > 0):
                    """ line_count += 1
                    content = content + [("$fwrite(f,\"%0t cycle :{}:{}\\n\"  , $time);\n").format(new_file,line_count+1)] """
                    content = content + [("{}\n").format(line)]
                    line_count += 1

                    """ elif line.find("assign") != -1 or(line.find("wire") != -1 and line.find("=") != -1):
                    content = content + [("{}\n").format(line)]
                    line_count += 1
                    content = content + ["always@* begin \n"]
                    line_count += 1
                    content = content + [("$fwrite(f,\"%0t cycle :{}:{}\\n\"  , $time);\n").format(new_file,line_count-1)]
                    line_count += 1
                    content = content + ["end\n"]
                    line_count += 1 """
                else:
                    content = content + [("{}\n").format(line)]
                    line_count += 1
        else:
            line = line.replace("\n",'')
            content = content + [("{}\n").format(line)]
            line_count += 1
        
        if re.search(r"\balways_ff[\w\W]+\bbegin\b", line):
            beginend_flag = beginend_flag + 1
        elif re.search(r"\bend\b[^\w\W]+\bbegin\b", line):
            None
        elif re.search(r"\bend\b", line) and (beginend_flag>0):
            beginend_flag = beginend_flag - 1
        elif re.search(r"\bbegin\b", line) and (beginend_flag>0):
            beginend_flag = beginend_flag + 1

    with open(new_file, "w") as writer:
        for line in content:
            writer.write(line)

    print("=================================== add_display done ======================================")


if __name__ =="__main__":
    parser = argparse.ArgumentParser(
                    prog = 'ibex_add_fwrite',
                    description = 'What the program does',
                    epilog = 'Text at the bottom of help')
    parser.add_argument('-r', '--rewrite_format',type=str, metavar='STRING')
    parser.add_argument('-c', '--construct_rwtable',action='store_true')
    args = parser.parse_args()
    
    
    if args.rewrite_format:
        re_file=args.rewrite_format
        sv_rewrite_format(re_file,re_file)
        add_display(re_file,re_file)
    elif args.construct_rwtable:
        rw_parse()
    
