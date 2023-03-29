import yaml
import json
import argparse
import subprocess
import re

class dep_node:
    def __init__(self, id=None, name='', dir=''):
        self.id = id
        self.name = name
        self.dir = dir
        self.children = []

def find_core_path(core_name): # input core_name "XX:XX:name:X" -> dir/name.core
    #print(core_name)

    file_name="*"+core_name.split(":")[2]+".core"
    command = ["fusesoc", "--cores-root=.", "core", "show", core_name]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
    core_root = re.search(r'(?<=Core root:)\s*[^\n]+(?=\n)', result).group(0).replace(" ",'')+"/"
    command = 'find . -name "'+file_name+'" | grep -E "^'+ core_root.replace(".","\.").replace("/","\/") +'[^/]+$"'
    output_bytes = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    output_str = output_bytes.decode('utf-8').strip()
    if('\n' in output_str):
        for s in output_str.split('\n'):
            if(s == core_root+core_name.split(":")[1]+"_"+core_name.split(":")[2]+".core"):
                out=s
            elif(s == core_root+core_name.split(":")[2]+".core"):
                out=s
    else:
        out = output_str

    #print(out)
    return out

def find_dep(core_dir): # input core_dir "core_dir/", "*name.core" -> dependency_list
    core=core_dir
    #print('[core_di]:'+core+'\n')
    with open(core, 'r') as file:
        try:
            yaml_data = yaml.safe_load(file)
            json_data = json.dumps(yaml_data)
            dict_data = json.loads(json_data)
        except yaml.YAMLError as e:
            print(e)

    if("filesets" in dict_data):
        if('files_rtl' in dict_data["filesets"]):
            if('depend' in dict_data["filesets"]['files_rtl']):
                if(type(dict_data["filesets"]['files_rtl']['depend']) is list):
                    return dict_data["filesets"]['files_rtl']['depend']
                else:
                    return [dict_data["filesets"]['files_rtl']['depend']]
    return []

def find_sv(core_dir): # input core_dir "core_dir/", "*name.core" -> dependency_list
    #print('[core_di]:'+core+'\n')
    with open(core_dir, 'r') as file:
        try:
            yaml_data = yaml.safe_load(file)
            json_data = json.dumps(yaml_data)
            dict_data = json.loads(json_data)
        except yaml.YAMLError as e:
            print(e)
    
    out_list = []
    new_out_list = []

    if("filesets" in dict_data):
        if('files_rtl' in dict_data["filesets"]):
            if('files' in dict_data["filesets"]['files_rtl']):
                if(type(dict_data["filesets"]['files_rtl']['files']) is list):
                    out_list = dict_data["filesets"]['files_rtl']['files']
                else:
                    out_list = [dict_data["filesets"]['files_rtl']['files']]
    for n in range(len(out_list)):
        if type(out_list[n]) is dict:
            out_list[n] = list(out_list[n].keys())[0]
        out_list[n] = core_dir.rsplit("/", 1)[0]+"/"+out_list[n]
    
    """ for i in out_list:
        new_out_list.append(re.search(r'[^ ]+', i).group(0))
 """
    return out_list
    

def build_dep_tree(top_core):
    dynamic_core_dir_list = [top_core]
    dynamic_core_name_list = []
    overall_core_dir_list = []

    while(dynamic_core_dir_list!=[]):
        for core_dir_to_find in dynamic_core_dir_list: # find out all the corename in the .core depend on dynamic_core_dir_list
            dynamic_core_name_list = dynamic_core_name_list+find_dep(core_dir_to_find)
        overall_core_dir_list = overall_core_dir_list + dynamic_core_dir_list
        dynamic_core_dir_list = []
        for core_name_to_find in dynamic_core_name_list:
            dynamic_core_dir_list.append(find_core_path(core_name_to_find))
        dynamic_core_name_list = []
        #print (dynamic_core_dir_list)

    new_core_dir_list=[]
    for i in overall_core_dir_list:
        if i not in new_core_dir_list:
            new_core_dir_list.append(i)

    return new_core_dir_list


if __name__=="__main__":

    parser = argparse.ArgumentParser(
                    prog = 'print_design_list',
                    description = 'What the program does',
                    epilog = 'Text at the bottom of help')

    parser.add_argument('filename')
    args = parser.parse_args()
    
    core_dir_list=build_dep_tree(args.filename)
    
    sv_list=[]
    for i in core_dir_list:
        sv_list=sv_list+find_sv(i)
    
    with open("sv_list","w") as f:
        for i in sv_list:
            if(i.endswith(".sv")):
                f.write(i+'\n')


