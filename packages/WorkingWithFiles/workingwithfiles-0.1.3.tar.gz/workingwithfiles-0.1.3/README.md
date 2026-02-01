# WorkingWithFiles

Functions to find and list files

## 1. Installing

To install the package from [PyPI](https://pypi.org/project/WorkingWithFiles/), follow the instructions below:


```bash
pip install --upgrade WorkingWithFiles
```

Execute `pip show WorkingWithFiles` to see where it was installed, probably in `/home/USERNAME/.local/lib/python3.10/site-packages/WorkingWithFiles`.

### Using

To start, use the command below:

```bash
import WorkingWithFiles as wwf

input_diretory_1 = "/some/path/with/images"
file_format_1    = ".png"

list_files = wwf.get_all_files_in_dir_list([input_diretory_1],formats_search=[file_format_1]);
```
## 2. More information

If you want more information go to [doc](https://github.com/trucomanx/WorkingWithFiles/blob/main/doc) directory.

## 3. Buy me a coffee

If you find this tool useful and would like to support its development, you can buy me a coffee!  
Your donations help keep the project running and improve future updates.  

[☕ Buy me a coffee](https://ko-fi.com/trucomanx) 

## 4. License

This project is licensed under the GPL license. See the `LICENSE` file for more details.
