#!/usr/bin/python

import os
import sys
from natsort import os_sorted


def rename_files_in(dirpath,prename,fmt_out=".jpg",formats_search=['.jpeg','.JPEG','.jpg','.JPG']):
    '''
    Renombra los archivos de forma ordenada usando un prename
    
    :param dirpath: Path a analizar.  
    :type dirpath: string
    :param prename: Nombre previo. Los nombres nuevos tendran la forma `prename+str(id)+fmt_out`.
    :type prename: string
    :param fmt_out: Formato de salida. Los nombres nuevos tendran la forma `prename+str(id)+fmt_out`.
    :type fmt_out: string
    :param formats_search: Lista de formatos aceptados.
    :type formats_search: list[string]
    :warning: El prename no debe ser el prename de los archivos actuales o seran sobrescritos varios archivos.
    '''
    print("Working on:",dirpath)
    if(os.path.isdir(dirpath)==False):
        print("Directory",dirpath,"no exist!");
        return 0;
    for x in os.walk(dirpath):
        print('Found some files:',x[2])
    
    if len(x[2])>0:
        k=1;
        for name in x[2]:
            #print("id:",k,"name:",os.path.join(dirpath,name),"out:",os.path.join(dirpath,prename+str(k)+fmt_out))
            filename, ext = os.path.splitext(name);
            if(ext in formats_search):
                os.rename(os.path.join(dirpath,name), os.path.join(dirpath,prename+str(k)+fmt_out))
                k=k+1;


def get_all_files_in_dir(dirpath,formats_search=['.jpeg','.JPEG','.jpg','.JPG'],is_relative=False):
    """
    Busca archivos.
    Retorna todos los archivos en el directorio `dirpath`.
    Restringe su busqueda a las extensiones en `formats_search`.
    
    :param dirpath: directorio
    :type dirpath: string
    :param formats_search: Lista de formatos
    :type formats_search: list[string]
    :param is_relative: habilita uma salida con la direción relativa a dirpath.
    :type is_relative: bool
    :return: Lista ordenada de todos los archivos en dirpath.
    :rtype: list[string]
    """
    lista=[];
    
    if(os.path.isdir(dirpath)==False):
        print("Directory "+dirpath+" no exist!", file=sys.stderr);
        sys.exit();
    for x in os.walk(dirpath):
        for name in x[2]:
            filename, ext = os.path.splitext(name);
            if(ext in formats_search):
                fpath=os.path.join(x[0],name);
                if is_relative:
                    fpath = os.path.relpath(fpath, dirpath)
                lista.append(fpath);
    return os_sorted(lista);


def get_all_files_in_dir_list(dirpath_list,formats_search=['.jpeg','.JPEG','.jpg','.JPG']):
    """
    Busca archivos.
    Retorna todos los archivos en los directorios listados en `dirpath_list`.
    Restringe su busqueda a las extensiones en `formats_search`.
    
    :param dirpath_list: lista de directorios
    :type dirpath_list: list[string]
    :param formats_search: Lista de formatos
    :type formats_search: list[string]
    :return: Lista ordenada de todos los archivos en dirpath_list.
    :rtype: list[string]
    """
    lista=[];
    for dirpath in dirpath_list:
        if(os.path.isdir(dirpath)==False):
            print("Directory "+dirpath+" no exist!", file=sys.stderr);
            sys.exit();
        for x in os.walk(dirpath):
            for name in x[2]:
                filename, ext = os.path.splitext(name);
                if(ext in formats_search):
                    lista.append(os.path.join(x[0],name));
    return os_sorted(lista);


def join_path_to_list_path(base_dir,list_path):
    """
    Agrega un `base_dir` a cada path en `list_path`.
    
    :param dirpath: Directorio base.
    :type dirpath: string
    :param list_path: Lista de directorios.
    :type list_path: list[string]
    :return: Lista de path con base_dir
    :rtype: list[string]
    """
    lista=[];
    for fpath in list_path:
        lista.append(os.path.join(base_dir,fpath));
    return lista;
    
def relpath_of_list_path(list_path,base_dir):
    """
    Retorna una lista de path relativa a `base_dir` desde una lista `list_path`.
    
    :param list_path: Lista de directorios.
    :type list_path: list[string]
    :param dirpath: Directorio base.
    :type dirpath: string
    :return: Lista de path relativo a base_dir
    :rtype: list[string]
    """
    lista=[];
    for fpath in list_path:
        lista.append(os.path.relpath(fpath, base_dir));
    return lista;
