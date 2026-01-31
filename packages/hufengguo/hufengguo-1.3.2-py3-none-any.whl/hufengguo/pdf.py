import fitz
from pypdf import PdfReader, PdfWriter
from .hufengguo import gen_pwd
from .filepath import my_exists


#--------------------------------------------------------------------
# 自定义函数：保护PDF文件
# 保护操作默认的权限是-3552：11111111111111111111001000100000
# 按默认权限保护之后：禁止复制、修改、打印、增删页面
#                     保留注释、填写表单域、签名和阅读辅助
#
# 我们以后可修改保护后的权限，不过需要提供所有者密码
#
# 我们还可以提供用户密码，保护之后打开PDF文件就需要提供用户密码
#
#--------------------------------------------------------------------
def protect_pdf(fnin, fnout, permission_value=-3552, user_pwd="", owner_pwd=None):
    # 读取原始PDF，创建新的PDF
    reader, writer = PdfReader(fnin), PdfWriter()
    
    # 复制所有页面到新PDF
    for page in reader.pages:
        writer.add_page(page)
    
    # 按照指定的权限加密PDF文件
    owner_pwd = str(owner_pwd) if owner_pwd else gen_pwd()
    writer.encrypt(
        user_password=user_pwd,        # 用户密码
        owner_password=owner_pwd,      # 所有者密码
        use_128bit=True,               # 使用128位加密
        permissions_flag=permission_value
    )
    
    # 保存加密后的PDF
    with open(fnout, "wb") as f:
        writer.write(f)


#----------------------------------------------------------------
# 读取PDF文件的权限值
# 返回字典 {True: 数字形式的权限值, False: "错误信息"}
#----------------------------------------------------------------
def get_pdf_permission_value(fnin, pwd=""):
    d = dict.fromkeys([True, False])
    if not my_exists(fnin)[0]:
        d[False] = f"文件 {fnin} 不存在！"
    else:
        with fitz.open(fnin) as pdf:
            if pdf.authenticate(pwd)==0:
                if pwd:
                    d[False] = f"您为文件 {fnin} 提供的密码 {pwd} 错误！"
                else:
                    d[False] = f"文件 {fnin} 存在密码，您没有提供密码！"
            r = pdf.permissions
            d[True] = r
    return d


#----------------------------------------------------------------
# 通过权限值分析PDF文件的权限
#----------------------------------------------------------------
def parse_pdf_permission_by_value(value):
    int32 = value & 0xFFFFFFFF
    d = {
        "打印": bool(int32 & (1<<2)),                     # 第2位，位置从0开始算
        "更改文档": bool(int32 & (1<<3)),                 # 第3位
        "文档组合": bool(int32 & (1<<3)) or               # 第3、10位
                    bool(int32 & (1<<10)),
        "内容复制": bool(int32 & (1<<4)),                 # 第4位
        "复制内容用于辅助工具": bool(int32 & (1<<3)) or   # 第3、9位
                                bool(int32 & (1<<9)),     # 第9位
        "注释": bool(int32 & (1<<5)),                     # 第5位
        "填写表单域": bool(int32 & (1<<3)) or             # 第3、5、8位
                      bool(int32 & (1<<5)) or
                      bool(int32 & (1<<8)),           
        "签名": bool(int32 & (1<<3)) or                   # 第3、5、8位，跟填写表单域一样
                bool(int32 & (1<<5)) or
                bool(int32 & (1<<8)),           
        "创建模板页面": bool(int32 & (1<<3)) or           # 第3、8位
                        bool(int32 & (1<<8)),
        "高质量打印": bool(int32 & (1<<11)),              # 第11位
        "权限值": value,
        "无符号权限值": int32,
        "二进制权限值": f"{int32:032b}",
    }
    return d


#----------------------------------------------------------------
# 获取PDF文件的权限，返回字典
#----------------------------------------------------------------
def get_pdf_permissions(fnpdf, pwd=""):
    d = get_pdf_permission_value(fnpdf, pwd=pwd)
    if d[False]:
        return {"error": d[False]}
    d = parse_pdf_permission_by_value(d[True])
    for key in d:
        if not key.endswith("权限值"):
            d[key] = "允许" if d[key] else "禁止"       
    return d


#----------------------------------------------------------------
# 解密PDF文件并去掉权限保护
#----------------------------------------------------------------
def decrypt_pdf(fnin, fnout, pwd=""):

    d = dict.fromkeys([True, False])
    if not my_exists(fnin)[0]:
        d[False] = f"文件 {fnin} 不存在！"
    else:
        try:
            with fitz.open(fnin) as pdf:
                pdf.authenticate(pwd)
                pdf.save(fnout)
                d[True] = f"成功解密PDF文件，保存为 {fnout} ！"
        except Exception as e:
            d[False] = f"文件 {fnin} 解密失败，出错信息如下：\n{e}"
    return d


if __name__ == "__main__":
    fnin = r"test.pdf"
    fnout = r"test_保护.pdf"
    protect_pdf(fnin, fnout)
    r = get_pdf_permissions(fnout)
    print(*r.items(), sep="\n")
    