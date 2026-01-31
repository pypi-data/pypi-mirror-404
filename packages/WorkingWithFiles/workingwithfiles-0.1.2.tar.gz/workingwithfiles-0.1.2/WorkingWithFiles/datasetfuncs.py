import pandas as pd
import os
import WorkingWithFiles.WorkingWithFiles as wf
import csv  
import numpy as np
from collections import Counter



def generate_csv_file_from_dir_structure(base_dir,format_list,csv_path,header = ['filename', 'label'],label_first=True):
    '''
    Generate a CSV file analyzing a directory structure from a root directory, 
    generates two columns a filepath column and a label column.
    The labels of columns can be defined in the parameter 'header'.

    base_dir: Base directory. ex:"/some/filepath"
    format_list: List string with all the file types. ex: ['.png','.PNG']
    csv_path: Path of CSV output file. ex: "/some/output/filepath/out.csv"
    header: List string with two elements, they are the headers of CSV file. ex: ['filename', 'label']
    label_first: Bool if True the label is the first subdirectory name, else the label is the last subdirectory name.
    '''
    ## find the labels with only the first level name directory
    label_list = [ name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name)) ];
    #print('label_list:',label_list)    
    
    ## Find all subdirectories
    file_list_list=[];    
    for label in label_list:
        tmp_path = os.path.join(base_dir,label);
        file_list = wf.get_all_files_in_dir(tmp_path,formats_search=format_list,is_relative=True);
        file_list_list.append(file_list);
    
    ## Write a CSV file
    with open(csv_path, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
    
        writer.writerow(header)
        
        Nel=[];
        for file_list in file_list_list:
            Nel.append(len(file_list));
            
        N=np.max(Nel);
        M=len(label_list);
        
        out=[]
        Count=Counter();
        for n in range(N):
            for m in range(M):
                if(n<Nel[m]):
                    filepath=os.path.join(label_list[m],file_list_list[m][n]);
                    
                    if label_first:
                        category=label_list[m];
                    else:
                        diretorio, nome_arquivo = os.path.split(filepath)
                        category=os.path.basename(diretorio);
                    
                    item=[filepath, category];
                    Count[category]=Count[category]+1;
                    
                    writer.writerow(item);
                    out.append(item);
    
    return out,Count;



def generate_csv_file_from_csv_dir_structure(   base_dir,
                                                format_list,
                                                csv_path,
                                                input_has_header= False,
                                                output_header_list = None,
                                                label_first=True,
                                                processing_func=None):
    '''
    Generate a CSV file analyzing a directory structure from a root directory with csv files (without labels only N data columns), 
    the function generates a CSV file with N data columns and a label column.
    The labels of columns can be defined in the parameter 'output_header_list'.

    base_dir: Base directory. ex:"/some/filepath"
    format_list: List string with all the file types. ex: ['.png','.PNG']
    csv_path: Path of CSV output file. ex: "/some/output/filepath/out.csv"
    input_has_header: Bool if True assumes that the input csv files have a header, else in another case.
    output_header_list: If None the output has no header, if 'default' the output has header ['d0',...,'dN-1','label'], if list string the list is used.
    label_first: Bool if True the label is the first subdirectory name, else the label is the last subdirectory name.
    processing_func: Function that proccess a dataframe (csv file)
    '''
    ## find the labels with only the first level name directory
    first_level_list = [ name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name)) ];
    #print('first_level_list:',first_level_list)    
    
    ## Find all subdirectories
    file_list_list=[];    
    for label in first_level_list:
        tmp_path = os.path.join(base_dir,label);
        file_list = wf.get_all_files_in_dir(tmp_path,formats_search=format_list,is_relative=True);
        file_list_list.append(file_list);
    
    ## Write a CSV file
    with open(csv_path, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)

        ##################################
        ## Finding and wrinting the output header list
        if output_header_list==None:
            pass;
        elif output_header_list=='default':
            filepath=os.path.join(first_level_list[0],file_list_list[0][0]);
            ## load df
            if input_has_header:
                df = pd.read_csv(os.path.join(base_dir,filepath))
            else:
                df = pd.read_csv(os.path.join(base_dir,filepath), header=None)
            
            oh_list=['d'+str(n) for n in range(df.shape[1])]+['label'];
            writer.writerow(oh_list);
        elif isinstance(output_header_list, list):
            writer.writerow(output_header_list)
        ##################################
        
        Nel=[];
        for file_list in file_list_list:
            Nel.append(len(file_list));
            
        N=np.max(Nel);
        M=len(first_level_list);
        
        out=[]
        Count=Counter();
        for m in range(M):
            for n in range(N):
                if(n<Nel[m]):
                    filepath=os.path.join(first_level_list[m],file_list_list[m][n]);
                    
                    ## load df
                    if input_has_header:
                        df = pd.read_csv(os.path.join(base_dir,filepath))
                    else:
                        df = pd.read_csv(os.path.join(base_dir,filepath), header=None)
                    ## processing df
                    if processing_func!=None:
                        df=processing_func(df);
                    
                    ## set category
                    if label_first:
                        category=first_level_list[m];
                    else:
                        diretorio, nome_arquivo = os.path.split(filepath)
                        category=os.path.basename(diretorio);
                    
                    df['label']=category;
                    
                    item=df.values.tolist();
                    Count[category]=Count[category]+df.shape[0];
                    
                    writer.writerows(item);
                    out.append(item);
    
    return out,Count;


