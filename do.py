import os
import traceback
import shutil
from pypinyin import pinyin, Style
import pandas as pd
from PIL import Image as img

def transit_file(behavior, src_path, dst_path, name, new_name=None):
    print('from : ',src_path)
    print('to : ',dst_path)
    if not new_name:    #rename the original file while proceeding.
        new_name = name
    try:
        # cmd = 'chmod -R +x ' + src_path
        # os.popen(cmd)
        f_src = os.path.join(src_path, name)
        if not os.path.exists(dst_path):
            os.mkdir(dst_path)
        f_dst = os.path.join(dst_path, new_name)
        if behavior == 'c':
            shutil.copyfile(f_src, f_dst)
        elif behavior == 'm':
            shutil.move(f_src, f_dst)
    except Exception as e:
        print('copy_file ERROR: ',e)
        traceback.print_exc()

cwd = os.getcwd()

src_dir = 'unicode_CH_heiti'
src_path = os.path.join(cwd, src_dir)

freq_name = 'CorpusCharacterlist.xls'
freq_path = os.path.join(cwd, freq_name)
freq_file = pd.read_excel(freq_path)
rank_dict = dict()
for i in freq_file.index:
    char = freq_file.loc[i]['char']
    rank = freq_file.loc[i]['rank']
    uni = ord(char) - int('4e00',16)
    info = {'char': char, 'rank': rank}
    rank_dict[uni] = info

locale_name = 'zh_CN'
cache_name = 'temp'
locale_path = os.path.join(cwd, locale_name)
cache_path = os.path.join(cwd, cache_name)

if os.path.exists(locale_path):
    shutil.rmtree(locale_path)

#Start: Categorize character according to its pinyin and tone, support heteronyms.
for png in os.listdir(src_path):
    name,ext = os.path.splitext(png)
    uni_int = int('4e00',16) + int(name)
    pyns = pinyin(chr(uni_int), style=Style.TONE3, heteronym=True, neutral_tone_with_five=True)[0]
    for pyn in pyns:
        valid = True
        for letter in pyn:
            if (ord(letter) not in range(65,90+1)) and (ord(letter) not in range(97, 122+1)) and (ord(letter) not in range(48, 57+1)):
                #os.remove(os.path.join(src_path, png))
                valid = False
                break
        if valid:
            py, n = pyn[:-1], pyn[-1]
            out_path = os.path.join(locale_path, py, n)
            if not os.path.exists(out_path):
                os.makedirs(out_path)
            transit_file('c', src_path, out_path, png)
#End

#Start: Re-rank the characters under each /pinyin/tone category according to their usage frequency record.
if os.path.exists(cache_path):
    shutil.rmtree(cache_path)
os.makedirs(cache_path)
uni_record = [key for key in rank_dict.keys()]
for root, dirs, files in os.walk(locale_path):
    if len(dirs) == 0:
        freq, uncommon = [],[]
        for png in files:
            name,ext = os.path.splitext(png)
            uni = int(name)
            if uni in uni_record:
                freq.append(uni)
            else:
                uncommon.append(uni)
        rank = [rank_dict[f]['rank'] for f in freq]
        unis_sorted = [i for _,i in sorted(zip(rank, freq))] + uncommon
        
        for uni in unis_sorted:
            ext = '.png'
            name = str(uni) + ext
            newname = str(len(os.listdir(cache_path))+1) + ext
            transit_file('m', root, cache_path, name, newname)
        for png in os.listdir(cache_path):
            #Start: Color treating
            img_path = os.path.join(cache_path, png)
            im = img.open(img_path)
            im = im.convert('RGBA')
            x, y = im.size
            for xpos in range(x):
                for ypos in range(y):
                    color = im.getpixel((xpos, ypos))
                    if color[0] < 10 and color[1] < 10 and color[2] < 10:
                        color = color[:-1] + (0,)
                        im.putpixel((xpos, ypos), color)
            im.save(img_path)
            #End
            transit_file('m', cache_path, root, png)
shutil.rmtree(cache_path)
#End