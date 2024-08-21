import sys
import os
import json
import re
import glob

# __GLOBAL VARS__
forceall = False
pflag = False
rflag = False
errflag = True
defcon = 0
with open("doctype_mapper.json") as doc_file:
    DOC_MAP = json.load(doc_file)
RECIPE_FILES = glob.glob("recipes/*.rp")
TAG_GROUPS = {
    "#fizzy": ["fizzy", "carbonated", "sparkling"]
}

# __MAIN__
def main(argc, argv):

    sys_args(argv)
    path_dict = recipe_crawl()
    for doctype in path_dict:
        rp_dict = database(DOC_MAP[doctype]['dbpath'], path_dict[doctype])
        for ID in rp_dict:
            writeHTML(rp_dict[ID])

# __ERROR HANDLING__
def throw_err(msg):

    if defcon == 0:
        exit("[SYNTAX ERROR] " + msg)
    if defcon == 1:
        exit("WARNING: ")
    if defcon == 2:
        return None

NO_ERROR = 0; MISSING_TYPE = 1; MULTI_TYPE = 2; NULL_TYPE = 3; TITLE_SUBHEADER = 4; TAG_SUBHEADER = 5; MULTI_SECT = 6
MISSING_TITLE = 7;
SYNTAX_ERROR = {
    MISSING_TYPE: lambda path: throw_err(f"[SYNTAX ERROR] Recipe \"{path}\" missing <!DOCTYPE [id]> statement"),
    MULTI_TYPE: lambda path: throw_err(f"[SYNTAX ERROR] Recipe \"{path}\" has multiple <!DOCTYPE [id]> statements"),
    NULL_TYPE: lambda path: throw_err(f"[SYNTAX ERROR] Recipe \"{path}\" has empty <!DOCTYPE [id]> statement"),
    TITLE_SUBHEADER: lambda path: throw_err(f"[SYNTAX ERROR] In Recipe \"{path}\": <title> block may not have subheaders. To add a subtitle, put it below the title in the <title> block"),
    TAG_SUBHEADER: lambda path: throw_err(f"[SYNTAX ERROR] In Recipe \"{path}\": tag blocks may not have subheaders"),
    MULTI_SECT: lambda path, block: throw_err(f"[SYNTAX ERROR] Recipe \"{path}\" has multipe \"{block}\" blocks that are indistinguishable. Please remove extra blocks or add/change subheaders."),
    MISSING_TITLE: lambda path: throw_err(f"[SYNTAX ERROR] Recipe \"{path}\" missing <title> block")
}

# __FUNCTIONS__

def sys_args(argv):

    global RECIPE_FILES
    global forceall
    global pflag
    global rflag
    global errflag

    if "--force-all" in argv:
        forceall = True
    if "--purge" in argv:
        pflag = True
    if "-r" in argv:
        index = argv.index("-r")
        rflag = True
    if "--recipe" in argv:
        index = argv.index("--recipe")
        rflag = True
    if rflag:
        try:
            file = open(argv[index+1], "r")
            file.close()
            RECIPE_FILES = [argv[index+1]]
            forceall = True
        except IndexError:
            print(f"-r/--recipe flag requires a recipe file")
        except FileNotFoundError:
            print(f"File {argv[index+1]} does not exist.")
    if "-ie" in argv or "--ignore-errors" in argv:
        errflag = False
        defcon = 2

def recipe_crawl():

    path_lst = []
    path_dict = {}
    for path in RECIPE_FILES:
        path_lst.append(path)
        rp = open(path)
        type = re.findall(r"<!DOCTYPE([^>]*)>\n", rp.read())
        if(len(type) < 1):
            SYNTAX_ERROR[MISSING_TYPE](path)
            continue
        if(len(type) > 1):
            SYNTAX_ERROR[MULTI_TYPE](path)
            continue
        if(type[0].strip() == ""):
            SYNTAX_ERROR[NULL_TYPE](path)
            continue

        path_dict[type[0][1:]] = path_dict.get(type[0][1:], []) + [path]
        rp.close()

    return path_dict

def database(dbpath, rp_paths):

    rp_dict = {}

    # Open the data file
    try:
        with open(dbpath, "r") as db_file:
            db = json.load(db_file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        db = {}

    try:
        with open("textbase.json", "r") as textbase_file:
            textbase = json.load(textbase_file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        textbase = {}

    # If the purge flag is set, remove pages whose recipe files have been deleted
    if pflag:
        flagged_ids = []
        for ID in db:
            if f"recipes\\{ID}.rp" not in rp_paths:
                try:
                    os.remove(f"/pages/{ID}.html")
                except:
                    pass
                flagged_ids.append(ID)
        for ID in flagged_ids:
            del db[ID]

    # Parse the rp files to create database
    for path in rp_paths:
        ID = path[-path[::-1].find('\\'):-(path[::-1].find(".")+1)]
        file = open(path, encoding="utf-8")
        text = file.read()
        if forceall or (ID not in db) or textbase.get(ID, "") != text:
            rp = parse_rp(ID, text)
            if rp != None:
                rp_dict[ID] = rp
                db[ID] = {
                'name': rp['title'],
                'tags': list(set(rp['tags'] + rp.get('itags', []) + rp.get('ingredient_tags',[]))),
                'otags': list(set(rp.get('otags', []) + rp.get('optional_tags', [])))
                }
                textbase[ID] = text
            print(path)
        file.close()

    # sort databases and dump to json
    db_sorted = {}
    textbase_sorted = {}
    for ID, data in sorted(db.items(), key=lambda x: x[1]['name']):
        db_sorted[ID] = data
    with open(dbpath, "w+") as db_file:
        json.dump(db_sorted, db_file, indent=4)

    for ID, data in sorted(textbase.items()):
        textbase_sorted[ID] = data
    with open("textbase.json", "w+") as textbase_file:
        json.dump(textbase_sorted, textbase_file, indent=4)

    return rp_dict

def parse_rp(ID, text):

    path = "recipes\\" + ID + ".rp"
    sections = re.findall(r"<([^>]*)>[^\*\n]*\n([^<]*)", text)
    rp = {"ID": ID}

    ingredient_reference = {}

    for s in sections:

        head = s[0].strip()
        body = s[1].strip()

        if " " in head:
            header = head[:head.find(" ")+1].strip()
            subheader = head[head.find(" ")+1:].strip()
            if subheader == "":
                subheader = "DEFAULT"
        else:
            header = head
            subheader = "DEFAULT"

        if header == "!DOCTYPE":
            if "!DOCTYPE" in rp:
                return SYNTAX_ERROR[MULTI_TYPE](path)
            if subheader == "DEFAULT":
                return SYNTAX_ERROR[NULL_TYPE](path)
            rp['DOCTYPE'] = subheader

        if header == 'title':
            if subheader != "DEFAULT":
                return SYNTAX_ERROR[TITLE_SUBHEADER](path)

            if "\n" not in body:
                rp['title'] = body
            else:
                rp['title'] = body[:body.find("\n")]
                rp['subtitle'] = body[body.find("\n")+1:]

        elif header in ['tags', 'itags', 'otags']:
            if subheader != "DEFAULT":
                return SYNTAX_ERROR[TAG_SUBHEADER](path)
            if header in rp:
                return SYNTAX_ERROR[MULTI_SECT](path, header)

            rp[header] = []
            for line in body.split("\n"):
                t = line.strip().lower()
                if t == "":
                    continue
                elif t[0] != "#":
                    rp[header].append(t)
                else:
                    rp[header] += TAG_GROUPS[t]

            rp[header] = sorted(rp[header])


        else:
            if header not in rp:
                rp[header] = {}
            if subheader in rp[header]:
                return SYNTAX_ERROR[MULTI_SECT](path, header)

            if header == 'ingredients':
                rp[header][subheader] = []
                for l in body.split("\n"):
                    line = l.strip()
                    if line != "":

                        rp['ingredient_tags'] = rp.get('ingredient_tags', []) + [t.strip().lower() for t in re.findall(r"{(?:tag:|#)([^@%}]*)}", line)]
                        rp['ingredient_tags'] = rp.get('ingredient_tags', []) + [t.strip().lower() for t in re.findall(r"{(?:tag:|#)(?:[^@%}]*)@([^}]*)}", line)]
                        rp['optional_tags'] = rp.get('optional_tags', []) + [t.strip().lower() for t in re.findall(r"{(?:tag:|#)(?:[^@%}]*)%([^}]*)}", line)]

                        tagged = line.split("*")
                        item = tagged[0].strip()

                        if len(tagged) > 1:
                            tag = tagged[1].strip()
                            ingredient_reference[tag] = item

                        rp[header][subheader].append(item)

            elif header == 'instructions':
                rp[header][subheader] = []
                for l in body.split("\n"):
                    line = l.strip()
                    shorts = re.findall(r"\*([A-Za-z_]*)", line)
                    for s in shorts:
                        line = line.replace(f"*{s}", ingredient_reference[s])
                    rp[header][subheader].append(line)
            else:
                rp[header][subheader] = body.split("\n")

    if 'DOCTYPE' not in rp:
        return SYNTAX_ERROR[MISSING_TYPE](path)
    if 'title' not in rp:
        return SYNTAX_ERROR[MISSING_TITLE](path)

    return rp

def writeHTML(rp_dict):

    doctype = rp_dict['DOCTYPE']

    htmlList = htmlBuilder(rp_dict)
    HTML = htmlJoin(htmlList)

    ID = rp_dict['ID']
    file = open(f"{DOC_MAP[doctype]['save_dir']}/pages/{ID}.html", "w+")
    file.write(HTML)
    file.close()

def htmlBuilder(rp):

    doctype = rp['DOCTYPE']

    html = [
        "<html>",
        "<head>",
        "<link rel=\"stylesheet\" href=\"../../main.css\">",
        "<script>function backHandler(event){window.location.href=\"" + DOC_MAP[doctype]["back_dir"] + "?tag=\"+sessionStorage.getItem(\"search\").replace(/\\//g, \"|\").replace(/&/g, \"+\");}</script>",
        f"<title>{rp['title']}</title>",
        "</head>",
        "<body>",
        "<button id=\"back\" onclick=\"backHandler()\">Back</button>",
        f"<h1>{rp['title']}</h1>"]

    if 'subtitle' in rp:
        html += [f"<h2>{rp['subtitle']}</h2><br>"]

    if 'tags' in rp:
        tags = ['<p>']
        for tag in rp['tags']:
            tags.append(f'<a href="{DOC_MAP[doctype]["back_dir"]}?tag={tag}" class="tags">#{tag}</a>')
        tags.append('</p>')
        html += tags

    if 'batch' in rp:
        batch = ['<h2>Batch and Time</h2>', '<p class="big-p">']
        batch += [l + "<br>" for l in rp['batch']['DEFAULT']]
        batch += ['</p>']
        html += batch

    if 'tools' in rp:
        tools = ["<h2>Equipment</h2>"]
        for subtitle in rp['tools']:
            if subtitle != 'DEFAULT':
                tools.append(f"<h3>{subtitle}</h3>")
            tools.append("<ul>")
            for t in rp['tools'][subtitle]:
                tools.append(f"<li>{t}</li>")
            tools.append("</ul>")
        html += tools

    if 'ingredients' in rp:
        ingredients = ["<h2>Ingredients</h2>"]
        for subtitle in rp['ingredients']:
            if subtitle != 'DEFAULT':
                ingredients.append(f"<h3>{subtitle}</h3>")
            ingredients.append("<ul>")
            for l in rp['ingredients'][subtitle]:

                l = re.sub(
                    r"{(?:tag:|#)([^@%}]*)(?:@|%)([^}]*)}",
                    lambda m: f'<a href="{DOC_MAP[doctype]["back_dir"]}?tag={m.group(2).strip().lower()}" style="color: #2c87f0; text-decoration: none">{m.group(1).strip()}</a>',
                    l)
                l = re.sub(
                    r"{(?:tag:|#)([^}]*)}",
                    lambda m: f'<a href="{DOC_MAP[doctype]["back_dir"]}?tag={m.group(1).strip().lower()}" style="color: #2c87f0; text-decoration: none">{m.group(1).strip()}</a>',
                    l)
                ingredients.append(f"<li>{l}</li>")
            ingredients.append("</ul>")
        html += ingredients

    if 'prep' in rp:
        prep = ["<h3>Preparation</h3>"]
        for subtitle in rp['prep']:
            if subtitle != 'DEFAULT':
                prep.append(f"<h4>{subtitle}</h4>")
            prep.append("<p class=\"Big-P\" style=\"margin-top: -5px; margin-left: 15px\">")
            for l in rp['prep'][subtitle]:
                prep.append(l + "<br>")
        prep.append("</p>")
        html += prep

    if 'instructions' in rp:
        instructions = ["<h2>Instructions</h2>"]
        for subtitle in rp['instructions']:
            if subtitle != 'DEFAULT':
                instructions.append(f"<h3>{subtitle}</h3>")
            instructions.append("<ol>")
            for l in rp['instructions'][subtitle]:

                l = re.sub(r"{(?:tag:|#)([^@%}]*)(?:@|%)([^}]*)}", r"\1", l)
                l = re.sub(r"{(?:tag:|#)([^}]*)}", r"\1", l)
                instructions.append(f"<li>{l}</li>")
            instructions.append("</ol>")
        html += instructions

    if 'notes' in rp:
        notes = ["<h2>Notes</h2>"]
        for subtitle in rp['notes']:
            if subtitle != 'DEFAULT':
                notes += [f"<h3>{subtitle}</h3>"]
            notes.append("<p>")
            for l in rp['notes'][subtitle]:
                l = re.sub(r"{link:([^}]*)}", r'<a href="\1">\1</a>', l)
                notes.append(l + "<br>")
            notes.append("</p>")
        html += notes

    html += ["</body>", "</html>"]
    return html

def htmlJoin(html_lst):

    html_str = "<!DOCTYPE html>\n"

    indent = 0
    for line in html_lst:

        if re.fullmatch("</[^<>]*>", line):
        #   print(line, "indent--")
            indent -= 1

        html_str += indent*"  " + line + "\n"
        if re.fullmatch("<[^/][^<>]*>", line) and line[:5] != '<link':
        #   print(line, "indent++")
            indent += 1

    return html_str


if __name__ == '__main__':
    main(len(sys.argv), sys.argv)
