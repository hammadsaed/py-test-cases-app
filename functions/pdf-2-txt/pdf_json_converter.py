"""
Python module to read the PDF and get the co-ordinates of block/line/word
"""
# -*- coding: utf-8 -*-
import json
import os

import unidecode
from pdfminer.layout import LTTextBoxHorizontal, LTTextBox, LTTextLine, LTTextBoxVertical,LTTextLine,LTImage
from pdfminer.layout import LTTextLineHorizontal
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.layout import LAParams, LTChar
from pdfminer.converter import PDFPageAggregator
import pdfminer
from pdfminer.converter import TextConverter
from io import StringIO
import boto3
# https://pdfminer-docs.readthedocs.io/programming.html#performing-layout-analysis

# from wfn_logging import wfn_logger
s3=boto3.resource('s3')

class PDF2JSONConverter:
    def __init__(self, bucket_name, logger, SOR=None):
        self.bucket_name = bucket_name
        self.wfn_logger = logger
        self.SOR = SOR
    

    def block_srt_left_to_right(self, lt_objs):
        lt_objs_temp = lt_objs
        for m, ob in enumerate(lt_objs_temp):
            if isinstance(ob, (LTTextBox, LTTextBoxHorizontal)):
                if m < (len(lt_objs_temp) - 1):
                    blk_co = [ob.bbox[0], ob.bbox[1], ob.bbox[2], ob.bbox[3]]
                    ob2 = lt_objs_temp[m + 1]
                    if isinstance(ob2, (LTTextBox, LTTextBoxHorizontal)):
                        blk_co2 = [ob2.bbox[0], ob2.bbox[1], ob2.bbox[2], ob2.bbox[3]]
                        if blk_co[3] == blk_co2[3] or blk_co[1] == blk_co2[1]:
                            if blk_co[2] > blk_co2[2]:
                                lt_objs_temp[m], lt_objs_temp[m + 1] = lt_objs_temp[m + 1], lt_objs_temp[m]
                                self.block_srt_left_to_right(lt_objs_temp)
    
        return lt_objs_temp

    # adding a comment
    def read_layout(self, lt_objs, w, h):
        block_final = []
        block_final_summary = []
    
        # Y axis sorting
        post_process = {}
        for ob in lt_objs:
            if isinstance(ob, (LTTextBox, LTTextBoxHorizontal)) and ob.get_text() != ' ':
                blk_co = [ob.bbox[0], ob.bbox[1], ob.bbox[2], ob.bbox[3]]
                post_process[ob] = h - blk_co[3]
        post_process  = {k: v for k, v in sorted(post_process.items(), key=lambda item: item[1], reverse=False)}
    
        sorted_objs = []
        for j in post_process.keys():
            sorted_objs.append(j)
    
        # for obj in sorted_objs:
        sorted_list = self.block_srt_left_to_right(sorted_objs)
        for obj in sorted_list:
            if isinstance(obj, (LTTextBox, LTTextBoxHorizontal)) and obj.get_text() != '':
                block_txt = obj.get_text().replace('\n', ' ')
                block_txt = unidecode.unidecode(block_txt)
                block_co = [obj.bbox[0], obj.bbox[1], obj.bbox[2], obj.bbox[3]]
                block_co = ' '.join([str(i) for i in block_co])
                line_final = []
                line_co = []
                for x in obj:
                    if isinstance(x, LTTextLineHorizontal):
                        line_text = x.get_text().replace('\n', ' ')
                        line_text = unidecode.unidecode(line_text)
                        line_co = [x.bbox[0], x.bbox[1], x.bbox[2], x.bbox[3]]
                        line_co = ' '.join([str(i) for i in line_co])
    
                    word = ''
                    words =[]
                    words_coor = []
                    word_final = []
                    word_coor = [10000,10000,-10000,-10000]
                    for y in x:
                        if isinstance(y, LTChar) and y.get_text().replace('\u00A0', ' ') != ' ':
                            word = word + y.get_text()
                            #03/02 Rama
                            # word_coor = [y.bbox[0], y.bbox[1], y.bbox[2], y.bbox[3]]
                            word_coor = [min(y.bbox[0],word_coor[0]),min((h - y.bbox[3]),word_coor[1]),max(y.bbox[2],word_coor[2]),max((h - y.bbox[1]),word_coor[3])]
     
                        else:
                            if word != '':
                                words.append(word)
                                word_coor = ' '.join([str(i) for i in word_coor])
                                words_coor.append(word_coor)
                                word = ''
                                word_coor = [10000,10000,-10000,-10000]
    
                    if len(words) == len(words_coor):
                        for i in range(len(words)):
                            word_dict = dict()
                            word_dict['Position'] = words_coor[i]
                            word_dict['Value'] = unidecode.unidecode(words[i])
                            word_final.append(word_dict)
                    
                    line_temp = dict()
                    line_temp[str(line_co)] = {'Word':word_final}
                    line_final.append(line_temp)
    
                block_temp = dict()
                block_temp['Position'] = block_co
                block_temp['Value'] = {'Line': line_final}
                
                block_temp_summary = dict()
                # block_temp[block_co] = {'Line': line_final}
                # block_temp[block_co] = {"txt": block_txt, "Line": line_final}
                block_temp_summary[block_co] = {"txt": block_txt}
                block_final.append(block_temp)
                block_final_summary.append(block_temp_summary)
    
            # if it's a container, recurse
            elif isinstance(obj, pdfminer.layout.LTFigure):
                self.read_layout(obj._objs,w,h)
    
        block_final = {'Block':block_final}
    
        return block_final, {'Block': block_final_summary}

    def pdf_to_text_by_page(self, fp, rsrcmgr, laparams, document_id, key_dir):
        retstr = StringIO()
        codec = 'utf-8'
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        # with open(path, 'rb') as fp:
        page_num = 1
        for page_number, page in enumerate(PDFPage.get_pages(fp, check_extractable=False), start=1):
            if page_number == page_num:
                try:
                    interpreter.process_page(page)
                    result_text = retstr.getvalue()
                except Exception as e:
                    result_text = ' '
                
                parent_dir = os.environ['PARENT_DIR']
                if self.SOR is not None:
                    parent_dir = f"{parent_dir}/{self.SOR}"
                BUCKET_NAME = self.bucket_name
                key_output = '{}/{}/{}-{}.txt'.format(parent_dir, key_dir, str(document_id), str(page_number).zfill(3))
                object = s3.Object(BUCKET_NAME,key_output)
                object.put(Body=result_text.encode('utf-8'))
                result_text = ''
                retstr.truncate(0)
                retstr.seek(0)
            page_num += 1
    
            
    def convert_pdf_to_json(self, fp, pdf_2_json_path, document_id, key_dir):
        result_flag = True
        try:
            rsrcmgr = PDFResourceManager()
            
            # line-margin, -L If two lines are are close together they are considered to be part of the same
            # paragraph. The margin is specified relative to the height of a line.
            # Default: 0.5
            laparams = LAParams(line_margin=0.1)
            
            # generate page level txt rollup
            self.pdf_to_text_by_page(fp, rsrcmgr, laparams, document_id, key_dir)
            
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
    
            parser = PDFParser(fp)
            document = PDFDocument(parser)
            
            password = ""
            caching = True
            final_result = []
            num_pages = 0
            for page in PDFPage.get_pages(fp, password=password,
                                          caching=caching, check_extractable=False):
                pdf_w = page.mediabox[2]
                pdf_h = page.mediabox[3]
                try:
                    interpreter.process_page(page)
                    layout = device.get_result()
                    result, result_summary = self.read_layout(layout._objs, pdf_w, pdf_h)
                except Exception as e:
                    result, result_summary = {'Block':[]}, {'Block':[]}
                final_result.append(result)
                num_pages += 1
                
                # write the file ( block level summary )
                BUCKET_NAME = self.bucket_name
                
                parent_dir = os.environ['PARENT_DIR']
                if self.SOR is not None:
                    parent_dir = f"{parent_dir}/{self.SOR}"
                key_output = '{}/{}/blocks/{}-pg{}-blocks.json'.format(parent_dir, key_dir, str(document_id), str(num_pages).zfill(3))
                
                object = s3.Object(BUCKET_NAME,key_output)
                object.put(Body=json.dumps(result_summary, indent=4))
    
            final_result = {'Page': final_result, "num_pages": num_pages}

            device.close()
            return final_result

        except Exception as e:
            # self.wfn_logger.error("Exception in converting PDF to JSON: {}".format(str(e)))
            # frame = getframeinfo(currentframe())
            # log.logError("DE-PDF-TO-JSON", " @ <File: {}: {}> Exception in converting PDF to JSON: {}".format(frame.filename.split(os.path.sep)[-1], frame.lineno, str(e)))
            result_flag = False
