import pdf2docx,xlrd,openpyxl,multiprocessing,hashlib,shutil,copy,warnings,threading,json,time
from pyquery import PyQuery as kcwebspq
from PIL import Image
from spire.pdf import *
def print_log(*strs):
    print(time.strftime("%Y-%m-%d %H:%M:%S"),*strs)
def img_is_con(image_path):
    """判断图片是否有内容"""
    img = Image.open(image_path)
    first_pixel = img.getpixel((0, 0))
    # 获取图片的宽度和高度
    width, height = img.size
    # 遍历图片的所有像素
    for x in range(width):
        for y in range(height):
            # 如果发现任何一个像素与第一个像素不同，则表示有内容
            if img.getpixel((x, y)) != first_pixel:
                return True
    # 如果所有像素都相同，则表示没有内容
    return False
def get_image_w_h(image_path):
    "获取图片宽高"
    with Image.open(image_path) as img:
        width, height = img.size
        return width, height

def json_decode(strs):
    """json字符串转python类型"""
    try:
        return json.loads(strs)
    except Exception as e:
        if 'JSON object must be str, bytes or bytearray, not list' in str(e):
            return strs
        return []
def json_encode(strs):
    """python列表或字典转成字符串"""
    try:
        return json.dumps(strs,ensure_ascii=False)
    except Exception:
        return ""
def get_file(folder='./',is_folder=True,suffix="*",lists=[],append=False):
    """获取文件夹下所有文件夹和文件

    folder 要获取的文件夹路径

    is_folder  是否返回列表中包含文件夹

    suffix 获取指定后缀名的文件 默认全部
    """
    if not append:
        lists=[]
    lis=os.listdir(folder)
    for files in lis:
        if os.path.isfile(folder+"/"+files):
            if suffix=='*':
                zd={"type":"file","path":folder+"/"+files,'name':files}
                lists.append(zd)
            else:
                if files[-(len(suffix)+1):]=='.'+str(suffix):
                    zd={"type":"file","path":folder+"/"+files,'name':files}
                    lists.append(zd)
        elif os.path.isdir(folder+"/"+files):
            if is_folder:
                zd={"type":"folder","path":folder+"/"+files,'name':files}
                lists.append(zd)
            get_file(folder+"/"+files,is_folder,suffix,lists,append=True)
        
    return lists
def file_set_content(filename,data,encoding="utf-8"):
    """写入文件内容
    
    filename 完整文件名

    data 要写入的内容

    encoding 保存编码
    """
    f=open(filename,'w',encoding=encoding)
    f.write(data)
    f.close()
    return True
def file_get_content(filename,cur_encoding='utf-8',encoding=False):
    """获取文件内容
    
    filename 完整文件名

    cur_encoding 指定编码获取文件内容

    encoding 是否返回文件编码  默认否
    """
    fileData=''
    if os.path.isfile(filename):
        if encoding:
            with open(filename, 'rb') as f:
                cur_encoding = chardet.detect(f.read())['encoding']
                # print_log('cur_encoding',cur_encoding)
        #用获取的编码读取该文件而不是python3默认的utf-8读取。
        with open(filename,encoding=cur_encoding) as file:
            fileData = file.read()
    if encoding:
        return fileData,cur_encoding
    else:
        return fileData
def md5(strs):
    """md5加密
    
    参数 strs：要加密的字符串

    return String类型
    """
    m = hashlib.md5()
    b = strs.encode(encoding='utf-8')
    m.update(b)
    return m.hexdigest()
def frgesregeeswfrgslkjhgfdertyu8765sdf44r56tg7uhik(pdfname,outname):
    # print_log('outname',outname)
    doc = PdfDocument()
    doc.LoadFromFile(pdfname)
    # print_log('outname',outname)
    doc.SaveToFile(outname, FileFormat.DOCX)
    doc.Close()
    # print_log('outname完成',outname)
def frgesregergslkjhgfdertyu876544r56tg7uhik(pdfname,outname):
    pdf = PdfDocument()
    # 加载PDF文件
    try:
        pdf.LoadFromFile(pdfname)
    except Exception as e:
        print_log('pdf to xlsx-eee',e)
        print_log('pdf to xlsx-pdfname',pdfname)
        if 'Arg_NullReferenceException:' in str(e) or 'Font parsing exception:' in str(e):
            if os.name != 'nt':
                file_set_content(outname+'err','error：需要在windows系统中完成')
                return False
            else:
                return False
        elif 'Windows Error 0xe06d7363' in str(e):
            return False
        else:
            raise Exception(e)
    else:
        total_pages = pdf.Pages.Count # 计算总页数
        pdf.Close()
    if total_pages<=10: #pdf小于10 直接转换
        pdf = PdfDocument()
        pdf.LoadFromFile(pdfname) # 加载PDF文档
        convertOptions = XlsxLineLayoutOptions(True, True, False, True, False) # 创建 XlsxLineLayoutOptions 对象来指定转换选项
        pdf.ConvertOptions.SetPdfToXlsxOptions(convertOptions) # 设置转换选项
        try:
            pdf.SaveToFile(outname,FileFormat.XLSX) # 将PDF文档保存为Excel XLSX格式
        except Exception as e:
            if 'Arg_NullReferenceException:' in str(e) or 'Font parsing exception:' in str(e):
                if os.name != 'nt':
                    file_set_content(outname+'err','error：需要在windows系统中完成')
                    return False
                else:
                    print_log('pdf to xlsx',e)
                    return False
            elif 'Windows Error 0xe06d7363' in str(e):
                print_log('pdf to xlsx',e)
                return False
            else:
                raise Exception(e)
        pdf.Close()
    else:
        out_path="app/runtime/temp/"+md5(pdfname)
        try:
            etx.split_pdf_by_page_count(input_file=pdfname,out_path=out_path,page_count=10)
            filearr=get_file(out_path)
            xlsxlists=[]
            for k in filearr:
                pdf = PdfDocument()
                pdf.LoadFromFile(k['path']) # 加载PDF文档
                convertOptions = XlsxLineLayoutOptions(True, True, False, True, False) # 创建 XlsxLineLayoutOptions 对象来指定转换选项
                pdf.ConvertOptions.SetPdfToXlsxOptions(convertOptions) # 设置转换选项
                pdf.SaveToFile(out_path+'/'+k['name']+'.xlsx', FileFormat.XLSX) # 将PDF文档保存为Excel XLSX格式
                pdf.Close()
                xlsxlists.append(out_path+'/'+k['name']+'.xlsx')
            workbook = openpyxl.Workbook()
            i=1
            for filename in xlsxlists:
                try:
                    wb = openpyxl.load_workbook(filename=filename)
                except Exception as e:
                    if 'Arg_NullReferenceException:' in str(e) or 'Font parsing exception:' in str(e):
                        if os.name != 'nt':
                            file_set_content(outname+'err','error：需要在windows系统中完成')
                            return False
                        else:
                            print_log('pdf to xlsx',e)
                            return False
                    elif 'Windows Error 0xe06d7363' in str(e):
                        print_log('pdf to xlsx',e)
                        return False
                    else:
                        raise Exception(e)
                else:
                    sheets =  wb.sheetnames
                    for sheet_name in sheets:
                        xls_sheet = wb[sheet_name]
                        xlsx_sheet = workbook.create_sheet(title='sheet'+str(i))
                        for row in xls_sheet.iter_rows():
                            for cell in row:
                                dst_cell = xlsx_sheet.cell(row=cell.row, column=cell.column)
                                dst_cell.value=copy.copy(cell.value)
                        i+=1
                try:
                    wb.close()
                except:pass
            workbook.save(outname)
            workbook.close()
        except Exception as e:
            if os.path.exists(out_path):
                shutil.rmtree(out_path)
            raise Exception(e)
        else:
            if os.path.exists(out_path):
                shutil.rmtree(out_path)
    return True
def lfjdsgjtr3535djdtdrgkrehsrsgtrssreiuiu43943uffh938raaqef(inputfile,outname):
    from spire import xls as spire_xls
    workbook = spire_xls.Workbook()
    workbook.LoadFromFile(inputfile)
    workbook.SaveToFile(outname, spire_xls.ExcelVersion.Version2016)
    workbook.Dispose()


def lfjdsgjtrdjdtdrgkgtrssreiuiu43943uffh938raaqef(xlsxfile,styles=True,imgpath=False,imgminsize=(10,10),outfiles=''):
    from spire import xls as spire_xls
    if imgpath:
        if imgpath[-1]=='/' or imgpath[-1]=='\\':
            imgpath=imgpath+md5(xlsxfile)+'/'
        else:
            imgpath=imgpath+'/'+md5(xlsxfile)+'/'
    try:
        work = openpyxl.load_workbook(filename=xlsxfile,data_only=True)
    except Exception as e:
        try:
            work.close()
        except:pass
        if 'list index out of range' in str(e) or 'Value does not match pattern' in str(e) or 'There is no item named' in str(e) or 'could be decompression bomb DOS attack' in str(e):
            work = xlrd.open_workbook(xlsxfile)
            sheet_names=work.sheet_names()
            work.release_resources()
            del work
        elif 'File is not a zip file' in str(e) or 'eaccf0860c6e23d9a1b3ad9140/c6ad59f6891fd0e3cf981e19f7af1802.xlsx' in xlsxfile:
            if outfiles:
                file_set_content(outfiles,'')
                return 
            else:
                raise Exception(e)
        elif 'File contains no valid workbook part' in str(e):
            if outfiles:
                file_set_content(outfiles,"error："+str(e))
                return
            else:
                raise Exception(e)
        else:
            print_log("openpyxl_1",e)
            raise Exception(e)
    else:
        sheet_names = work.sheetnames
        work.close()
    sheetarr=[]
    index=0
    for sheet in sheet_names:
        sheetarr.append({
            'sheet':sheet,
            'index':index
        })
        index+=1
    outfile='fileextclass/'+md5(xlsxfile)
    workbook = spire_xls.Workbook()
    # workbook = xls.Workbook()
    try:
        workbook.LoadFromFile(xlsxfile)
    except Exception as e:
        print_log("LoadFromFile_e",e)
        if 'at Internal.Runtime.CompilerHelpers.ThrowHelpers.ThrowIndexOutOfRangeException' in str(e):
            if outfiles:
                file_set_content(outfiles,"error："+str(e))
                return
            else:
                raise Exception(e)
        elif 'Arg_NullReferenceException:   at sprfgv.sprq(String) + 0xa' in str(e):
            file_size = os.stat(xlsxfile).st_size
            if file_size<1024*10:
                if outfiles:
                    file_set_content(outfiles,'')
                    return
                else:
                    raise Exception(e)
            else:
                raise Exception(e)
        else:
            raise Exception(e)
    else:
        for item in sheetarr:
            # print_log('item',item)
            if 'hiddenSheet'==item['sheet'] or ('fd9f959560a0a6a51c32808907cac60f.xlsx' in xlsxfile or '52b0b52931a669832c93873c1740b1.xlsx' in xlsxfile) and item['index']==2:
                html=''
            else:
                # print_log('item',item,xlsxfile)
                sheet = workbook.Worksheets[item['index']]
                try:
                    sheet.SaveToHtml(outfile+"/"+str(item['index'])+".html")
                except Exception as e:
                    if os.path.exists(outfile):
                        shutil.rmtree(outfile)
                    print_log("SaveToHtml_e",e)
                    if 'Arg_NullReferenceException:   at sprd1q.spra(Stream, sprd33, String, HTMLOptions) + 0x3c0b' in str(e):
                        warnings.warn(str(e))
                        html=''
                    else:
                        if outfiles:
                            file_set_content(outfiles,"error："+str(e))
                            return
                        else:
                            raise Exception(e)
                else:
                    html=file_get_content(outfile+"/"+str(item['index'])+".html")
                # print_log('item_2',item,xlsxfile)
            if html and styles:
                htmls=''
                # print_log('item_3',item,xlsxfile)
                doc=kcwebspq(html.replace(' ',' ').replace('  ',' ').replace('\xa0',' ').replace('xmlns="http://www.w3.org/1999/xhtml"',''))
                doc('style').remove()
                doc('head').remove()
                doc('*').removeAttr('style')
                doc('*').removeAttr('class')
                # doc('td').attr('style','border: 1px solid #ccc')
                # doc('table').attr('style','border-collapse: collapse;')
                if doc("font").length:
                    for k in doc("font").items():
                        k.replaceWith(k.html())
                if doc("b").length:
                    for k in doc("b").items():
                        k.replaceWith(k.html())
                if doc("body").length:
                    for k in doc("body").items():
                        k.replaceWith(k.html())
                if doc("div").length:
                    for k in doc("div").items():
                        k.replaceWith(k.html())
                for k in doc('col').items():
                    if not k.text():
                        k.remove()
                # print_log('item_4',item,xlsxfile)
                table=doc('table')
                for k in doc('h2').items():
                    h2text=k.text()
                    if 'Evaluation' in h2text and 'Warning' in h2text and 'Spire.XLS' in h2text:
                        k.remove()
                for div in doc('div').items():
                    divs=div.text().replace(' ','').replace('\n','')
                    if not divs:
                        div.remove()
                # print_log('item_5',item,xlsxfile)
                for tables in table.items():
                    tr=tables.find("tr")
                    trindex=0
                    for trs in tr.items():
                        trtext=trs.text()
                        if 'Evaluation' in trtext and 'Warning' in trtext and 'Spire.PDF' in trtext:
                            trs.remove()
                        elif not trtext:
                            if trindex>=tr.length-1:
                                trs.remove()
                        trindex+=1
                # print_log('item_6',item,xlsxfile)
                for k in doc('table tr').items():
                    if '扫描全能王创建' == k.text().replace(' ','').replace('\n','').replace('&nbsp;','').replace(' ','').replace('  ','').replace('\xa0',''):
                        k.remove()
                # doc('#deletetr').remove()
                #删除空列 左到右
                table=doc('table')
                for items in table.items():
                    count=items.find('tr').eq(0).find('td').length
                    if not count:
                        count=0
                    count+=20
                    tempsl=0
                    for sl in range(count): #删除空列全部
                        tempsl+=1
                        if not items.find("tr td:nth-child("+str(tempsl)+")").text().replace(' ',''):
                            items.find("tr td:nth-child("+str(tempsl)+")").remove()
                            tempsl-=1
                        else:
                            break
                        
        
                htmls=doc.html()
                if not htmls:
                    htmls=''
            elif html:
                htmls=''
                doc=kcwebspq(html)
                # doc('style').remove()
                # doc('head').remove()
                for k in doc('p').items():
                    if '扫描全能王创建' == k.text().replace(' ','').replace('\n','').replace('&nbsp;','').replace(' ','').replace('  ','').replace('\xa0',''):
                        k.remove()
                if doc("body").length:
                    for k in doc("body").items():
                        k.replaceWith(k.html())
                htmls=doc.html()
                if not htmls:
                    htmls=''
            else:
                htmls=''
            item['html']=htmls
        workbook.Dispose()
        sheetarr1=[]
        if True:
            for k in sheetarr:
                if k['html']:
                    doc=kcwebspq("<div>"+k['html']+"</div>")
                    img=doc('img')
                    for kk in img.items():
                        src=kk.attr("src").replace('\\','/')
                        w,h=get_image_w_h(outfile+'/'+src)
                        if w==674 and h==98 or not img_is_con(outfile+'/'+src):
                            kk.remove()
                        elif w<imgminsize[0] or h<imgminsize[1]:
                            kk.remove()
                        elif not imgpath:
                            kk.attr("desc","不提取")
                            kk.attr("src","")
                        else:
                            kk.attr("name","local_image")
                            imgsrc=imgpath+src
                            tar=imgsrc.split('/')
                            directory=''
                            i=0
                            while i<len(tar)-1:
                                directory+=tar[i]+'/'
                                i+=1
                            if not os.path.exists(directory):
                                os.makedirs(directory)
                            shutil.move(outfile+'/'+src, imgsrc)
                            kk.attr("src",imgsrc)
                    k['html']=doc.html()
                    sheetarr1.append(k)
        else:
            for k in sheetarr:
                if k['html']:
                    doc=kcwebspq("<div>"+k['html']+"</div>")
                    doc('img').remove()
                    k['html']=doc.html()
                    sheetarr1.append(k)
        if os.path.exists(outfile):
            shutil.rmtree(outfile)
        if outfiles:
            file_set_content(outfiles,json_encode(sheetarr1))
        else:
            return sheetarr1
def esgsvesgrhghtsezgesgrezgseszgrgesresgrges(input_file,out_path,page_count=1):
    # 创建PdfDocument对象
    pdf = PdfDocument()
    # 加载PDF文件
    try:
        pdf.LoadFromFile(input_file)
    except Exception as e:
        raise Exception(e)
    else:
        total_pages = pdf.Pages.Count # 计算总页数
    if total_pages<page_count:
        if not os.path.isdir(out_path):
            os.makedirs(out_path)
        shutil.copy(input_file, out_path)
    else:
        # 按指定页数拆分PDF
        for i in range(0, total_pages, page_count):
            # 创建新的PdfDocument对象
            new_pdf = PdfDocument()
            # 计算当前要插入的页码范围
            start_page = i
            end_page = min(i + page_count - 1, total_pages - 1)  # 确保不超过总页数
            try:
                # 将当前页码范围的页面插入到新PDF中
                new_pdf.InsertPageRange(pdf, start_page, end_page)
            except:pass
            else:
                # 保存生成的文件
                new_pdf.SaveToFile(out_path+"/" + f"{start_page + 1}-{end_page + 1}页.pdf")
                # 关闭新创建的PdfDocument对象
                new_pdf.Close()
        pdf.Close()

def rggestrsgrhklhtrdhbithjtiorjhiothposzfsgrgtsre(docfile,imgpath=False,imgminsize=(10,10),outfiles=''):
    """doc转html
    
    imgpath 是否保留图片 需要保存时传保存目录 以 / 结尾

    imgminsize 忽略 宽高 多少以下的图片

    return 返回格式 html 字符串
    """
    if imgpath:
        if imgpath[-1]=='/' or imgpath[-1]=='\\':
            imgpath=imgpath+md5(docfile)+'/'
        else:
            imgpath=imgpath+'/'+md5(docfile)+'/'
    outfile='fileextclass/'+md5(docfile)
    from spire import doc as spire_doc
    try:
        document = spire_doc.Document()
        document.LoadFromFile(docfile)
        document.SaveToFile(outfile+'/temp.html', spire_doc.FileFormat.Html)
        document.Close()
    except Exception as e:
        if outfiles:
            file_set_content(outfiles,"error："+str(e))
            return
        else:
            raise Exception(e)
    html=file_get_content(outfile+'/temp.html')
    doc=kcwebspq(html.replace(' ',' ').replace('  ',' ').replace('\xa0',' ').replace('xmlns="http://www.w3.org/1999/xhtml"',''))
    doc('title').remove()
    doc('style').remove()
    doc('head').remove()
    doc('*').removeAttr('style')
    doc('*').removeAttr('class')
    if doc("span").length:
        for k in doc("span").items():
            k.replaceWith(k.html())
    if doc("td p").length:
        for k in doc("td p").items():
            k.replaceWith(k.html())
    if doc("body").length:
        for k in doc("body").items():
            k.replaceWith(k.html())
    
    html=doc.html()
    if not html:
        html=''
    html=html.replace('<p>Evaluation Warning: The document was created with Spire.Doc for Python.</p>','').replace('<div/>','')
    html=html.replace('<p><ins data-userid="0" data-username="徐建清" data-time="0001-01-01T00:00:00Z">Evaluation Warning: The document was created with Spire.Doc for Python.</ins></p>','')
    html=html.replace('Evaluation Warning: The document was created with Spire.Doc for Python.','')
    if True:
        if html:
            doc=kcwebspq("<div>"+html+"</div>")
            img=doc('img')
            for kk in img.items():
                src=kk.attr("src").replace('\\','/')
                w,h=get_image_w_h(outfile+'/'+src)
                if w==674 and h==98 or not img_is_con(outfile+'/'+src):
                    kk.remove()
                elif w<imgminsize[0] or h<imgminsize[1]:
                    kk.remove()
                elif not imgpath:
                    kk.attr("desc","不提取")
                    kk.attr("src","")
                else:
                    kk.attr("name","local_image")
                    imgsrc=imgpath+src
                    tar=imgsrc.split('/')
                    directory=''
                    i=0
                    while i<len(tar)-1:
                        directory+=tar[i]+'/'
                        i+=1
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    shutil.move(outfile+'/'+src, imgsrc)
                    kk.attr("src",imgsrc)
            html=doc.html()
    else:
        if html:
            doc=kcwebspq("<div>"+html+"</div>")
            doc('img').remove()
            for k in doc('p').items():
                t=k.text()
                if t:
                    t=t.replace(' ','').replace('  ','').replace('\xa0','').replace(' ','')
                if not t:
                    k.remove()
            if doc.text():
                html=doc.html()
            else:
                html=''
    shutil.rmtree(outfile)
    doc=kcwebspq(html)
    #删除空行
    doc('table').attr("border","1")
    table=doc('table')
    for tables in table.items():
        for trs in tables.find("tr").items():
            trstext=trs.text()
            if trstext:
                trstext=trstext.replace('\n','').replace(' ','').replace(' ','').replace('  ','').replace('\xa0','')
            tempimgsrcstr=trs.html()
            if tempimgsrcstr:
                tempimgsrcstr=tempimgsrcstr.replace(' ','')
            else:
                tempimgsrcstr=''
            if not trstext and '<imgsrc=' not in tempimgsrcstr:
                trs.remove()
    html=doc("*").html()
    if outfiles:
        file_set_content(outfiles,html)
    else:
        return html
thread_exception = None
def fesgrsgtrgtdrhbtdgrrgrgsgtsegr(pdfname,outname):
    """pdf转docx
    
    pdfname pdf文件

    outname 转换后保存文件
    """
    global thread_exception
    try:
        folder_path=os.path.dirname(outname)
        if folder_path and not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        cv = pdf2docx.Converter(pdfname)
        cv.convert(outname, start=0, end=None)
        cv.close()
    except Exception as e:
        thread_exception = e
    return True
class etx:
    def get_image_w_h(image_path):
        return get_image_w_h(image_path=image_path)
    def tran_pdf_to_docx(pdfname,outname,timeout=None):
        """pdf转docx
        
        pdfname pdf文件

        outname 转换后保存文件

        timeout 转换超时 单位秒
        """
        if threading.current_thread().name!='MainThread' or not timeout:
            folder_path=os.path.dirname(outname)
            if folder_path and not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
            cv = pdf2docx.Converter(pdfname)
            cv.convert(outname, start=0, end=None)
            cv.close()
            return True
        else:
            global thread_exception
            thread_exception=None
            if not os.path.exists(pdfname):
                raise Exception("no such file: '"+pdfname+"'")
            thread = threading.Thread(target=fesgrsgtrgtdrhbtdgrrgrgsgtsegr,args=(pdfname,outname),daemon=True)
            thread.start()
            try:
                thread.join(timeout=timeout)
                if thread.is_alive():
                    thread.join()
                    raise Exception('tran_pdf_to_docx timeout out')
                else:
                    if thread_exception:
                        raise Exception(thread_exception)
                    return True
            except KeyboardInterrupt:
                thread.join()
                
    def tran_pdf_to_xlsx_process(pdfname,outname,process=True,timeout=300):
        """pdf 转 xlsx
        
        pdfname pdf文件

        outname 转换后保存地址

        timeout 转换超时 单位秒
        """
        print_log('tran_pdf_to_xlsx_process',pdfname)
        if os.path.exists(outname):
            raise Exception('outname：'+outname+' 已存在')
        if threading.current_thread().name!='MainThread' or (not process and not timeout):
            frgesregergslkjhgfdertyu876544r56tg7uhik(pdfname,outname)
            sheetarr=file_get_content(outname+'err')
            if 'error：'==sheetarr[0:6]:
                os.remove(outname+'err')
                raise Exception(sheetarr)
            return True
        else:
            p=multiprocessing.Process(target=frgesregergslkjhgfdertyu876544r56tg7uhik,args=(pdfname,outname),daemon=True)
            p.start()
            # print_log('timeout1',timeout)
            p.join(timeout=timeout)
            # print_log('timeout2',timeout)
            if p.is_alive():
                p.join()
                raise Exception('tran_pdf_to_xlsx_process timeout out')
            
            if os.path.exists(outname):
                sheetarr=file_get_content(outname+'err')
                if 'error：'==sheetarr[0:6]:
                    os.remove(outname+'err')
                    raise Exception(sheetarr)
                return True
            elif os.path.exists(outname+'err'):
                sheetarr=file_get_content(outname+'err')
                if 'error：'==sheetarr[0:6]:
                    os.remove(outname+'err')
                    raise Exception(sheetarr)
            else:
                return False
    def tran_pdf_to_docx_process(self,pdfname,outname,process=True,timeout=300):
        """pdf 转 docx
        
        pdfname pdf文件

        outname 转换后保存地址

        timeout 转换超时 单位秒
        """
        if threading.current_thread().name!='MainThread':
            process=False
        if os.path.exists(outname):
            raise Exception('outname：'+outname+' 已存在')
        if process:
            p=multiprocessing.Process(target=frgesregeeswfrgslkjhgfdertyu8765sdf44r56tg7uhik,args=(pdfname,outname),daemon=True)
            p.start()
            p.join(timeout=timeout)
            if p.is_alive():
                p.join()
                raise Exception('tran_pdf_to_docx_process timeout out')
            if os.path.exists(outname):
                return True
            else:
                return False
        else:
            frgesregeeswfrgslkjhgfdertyu8765sdf44r56tg7uhik(pdfname,outname)
            return True
    def tran_xlsx_to_html_process(xlsxfile,styles=True,imgpath=False,imgminsize=(10,10),timeout=300):
        """xlsx 转 html
        
        xlsxfile pdf文件

        styles 是否处理样式

        imgpath 是否保留图片 需要保存时传保存目录 以 / 结尾

        imgminsize 忽略 宽高 多少以下的图片

        timeout 转换超时 单位秒

        return 返回格式 [{'sheet':'','index':0,'','html':''}]
        """
        outfiles='fileextclass/'+md5(xlsxfile)+'.html'
        print_log('tran_xlsx_to_html_process',xlsxfile)
        if threading.current_thread().name!='MainThread':
            return lfjdsgjtrdjdtdrgkgtrssreiuiu43943uffh938raaqef(xlsxfile,styles,imgpath,imgminsize)
        else:
            p=multiprocessing.Process(target=lfjdsgjtrdjdtdrgkgtrssreiuiu43943uffh938raaqef,args=(xlsxfile,styles,imgpath,imgminsize,outfiles),daemon=True)
            p.start()
            p.join(timeout=timeout)
            if p.is_alive():
                p.join()
                raise Exception('tran_xlsx_to_html_process timeout out')
            
            if os.path.exists(outfiles):
                print_log('tran_xlsx_to_html_process_outfiles',outfiles)
                sheetarr=file_get_content(outfiles)
                os.remove(outfiles)
                if 'error：'==sheetarr[0:6]:
                    raise Exception(sheetarr)
                sheetarr=json_decode(sheetarr)
                return sheetarr
            else:
                raise Exception('tran_xlsx_to_html_process失败')
    def tran_doc_to_html_process(docfile,imgpath=False,imgminsize=(10,10),timeout=300):
        """doc 转 html  （注意：linux 系统中可能会报Cannot found font installed on the system错误，可以把windows系统的字体安装到linux中，安装命令参考 “mkfontdir 字体目录”）
        
        docfile doc文件

        imgpath 是否保留图片 需要保存时传保存目录 以 / 结尾

        imgminsize 忽略 宽高 多少以下的图片

        timeout 转换超时 单位秒

        return 返回格式 html 字符串
        """
        # if threading.current_thread().name!='MainThread':
        #     print_log('tran_doc_to_html_threading',docfile)
        #     return rggestrsgrhklhtrdhbithjtiorjhiothposzfsgrgtsre(docfile,imgpath,imgminsize)
        # else:
        print_log('tran_doc_to_html_process',docfile)
        outfiles='fileextclass/'+md5(docfile)+'.html'
        p=multiprocessing.Process(target=rggestrsgrhklhtrdhbithjtiorjhiothposzfsgrgtsre,args=(docfile,imgpath,imgminsize,outfiles),daemon=True)
        p.start()
        p.join(timeout=timeout)
        if p.is_alive():
            p.join()
            raise Exception('tran_doc_to_html_process timeout out')
        
        if os.path.exists(outfiles):
            html=file_get_content(outfiles)
            os.remove(outfiles)
            if 'error：'==html[0:6]:
                raise Exception(html)
        else:
            raise Exception('tran_doc_to_html_process失败')
        return html


    def split_pdf_by_page_count(input_file,out_path,page_count=1,timeout=300):
        """ pdf文件拆分
        
        input_file 文件名

        out_path 输出目录

        page_count 按多页拆分

        timeout 转换超时 单位秒
        """
        print_log('split_pdf_by_page_count')
        if os.name == 'nt' or (threading.current_thread().name!='MainThread'):
            process=False
        else:
            process=True
        if process:
            p=multiprocessing.Process(target=esgsvesgrhghtsezgesgrezgseszgrgesresgrges,args=(input_file,out_path,page_count),daemon=True)
            p.start()
            p.join(timeout=timeout)
            if p.is_alive():
                p.join()
                raise Exception('split_pdf_by_page_count timeout out')
            
            return True
        else:
            return esgsvesgrhghtsezgesgrezgseszgrgesresgrges(input_file,out_path,page_count)

