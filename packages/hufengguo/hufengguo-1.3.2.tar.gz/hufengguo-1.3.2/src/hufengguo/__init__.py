from .hufengguo import (
    mysum,
    isprime,
    find_files_listdir,
    find_files_walk,
    my_path2path,

    my_abspath,
    my_desktop_path,
    make_dir_exists,
    my_read_from_txtfile,
    my_read_from_txtfile_for_cn,
    my_write_to_txtfile,

    seg_by_jieba,
    segtag_by_jieba,
    seg_str_by_jieba,
    lseg_str_by_jieba,
    segtag_str_by_jieba,
    lsegtag_str_by_jieba,

    remove_white_from_text,
    gen_pwd,
)

from .hanzidigit import ( 
    hanzi2digit,
    digit2hanzi,
    da2xiao,
    xiao2da, 
    fenjie_nummber,
)

from .filepath import (
    my_exists,
    my_shutil_rmtree,
    my_os_remove,
)

from .filepathwindow import ( 
    MyFilePathWindow,
)


#====================================================
# 处理可选依赖中的函数
try:
    from .pdf import (
        protect_pdf,
        get_pdf_permission_value,
        parse_pdf_permission_by_value,
        get_pdf_permissions,
        decrypt_pdf,
    )
    HAS_PDF = True
except ImportError:
    # 定义占位符或空函数
    HAS_PDF = False
    
    # 提供友好的错误提示
    def _pdf_feature_not_available(*args, **kwargs):
        raise ImportError(
            "PDF处理功能需要额外的依赖。"
            "请安装: pip install hufengguo[pdf]"
        )
    
    # 创建占位符函数
    protect_pdf = _pdf_feature_not_available
    get_pdf_permission_value = _pdf_feature_not_available
    parse_pdf_permission_by_value = _pdf_feature_not_available
    get_pdf_permissions = _pdf_feature_not_available
    decrypt_pdf = _pdf_feature_not_available

