import sys
import os
import json
import re
import glob

recipe_files = glob.glob("recipes/*.rp")

def main():

	forceall, verbose, rflag = sys_args()

	try:
		with open("rpbase.json", "r+") as rpbase_file:
			rpbase = json.load(rpbase_file)
	except (FileNotFoundError, json.decoder.JSONDecodeError):
		rpbase = {}

	if not rflag:
		flagged_ids = []
		for ID in rpbase:
			if f"recipes/{ID}.rp" not in recipe_files:
				try:
					os.remove(f"recipe_data/{ID}.json")
				except:
					pass
				try:
					os.remove(f"pages/{ID}.html")
				except:
					pass
				flagged_ids.append(ID)
		for ID in flagged_ids:
			del rpbase[ID]

	for path in recipe_files:
		ID = path[-path[::-1].find('\\'):-(path[::-1].find(".")+1)]
		if (ID not in rpbase) or forceall:
			recipe_dict = parse_rp(ID)
			if verbose:
				print(f"{recipe_dict['title']}")
			rpbase[ID] = {'name': recipe_dict['title'], 'tags': list(set(recipe_dict['tags'] + recipe_dict.get('itags', []) + recipe_dict.get('ingredient_tags',[])))}
			#print(rpbase[ID])

			#writeJSON(recipe_dict)
			writeHTML(recipe_dict)



		#TODO: Clean any JSON or HTML files that don't have .rp entries.

	with open("rpbase.json", "w") as rpbase_file:
		json.dump(rpbase, rpbase_file, indent=4)
	
def sys_args():

	global recipe_files

	forceall = False
	verbose = False
	rflag = False

	if "-v" in sys.argv or "--verbose" in sys.argv:
		verbose = True

	if "--force-all" in sys.argv:
		forceall = True

	if "-r" in sys.argv:
		index = sys.argv.index("-r")
		rflag = True

	if "--recipe" in sys.argv:
		index = sys.argv.index("--recipe")
		rflag = True

	if rflag:
		try:
			file = open(sys.argv[index+1], "r")
			file.close()
			recipe_files = [sys.argv[index+1]]
			forceall = True
		except IndexError:
			print(f"--file flag requires a file parameter")
		except FileNotFoundError:
			print(f"File {sys.argv[index+1]} does not exist.")

	return forceall, verbose, rflag

def parse_rp(ID):

	file = open(f"recipes/{ID}.rp")
	raw = file.read()

	sections = re.findall("<(.*)>\n([^<]*)", raw)
	
	recipe_dict = {"id": ID}
	ingredient_reference = {}

	for s in sections:

		head = s[0].strip()
		body = s[1].strip()
		if " " in head:
			title = head[:head.find(" ")+1].strip()
		else:
			title = head

		if title != head:
			subtitle = head[head.find(" ")+1:].strip()
		else:
			subtitle = "default"

		if title == 'title':
			if "\n" not in body:
				recipe_dict['title'] = body
			else:
				recipe_dict['title'] = body[:body.find("\n")]
				recipe_dict['subtitle'] = body[body.find("\n")+1:]

		elif title == 'tags':
			recipe_dict['tags'] = [t.strip().lower() for t in body.split("\n") if t.strip() != ""]

		elif title == 'itags':
			recipe_dict['itags'] = [t.strip().lower() for t in body.split("\n") if t.strip() != ""]
 
		else:
			if title not in recipe_dict:
				recipe_dict[title] = {}

			if subtitle in recipe_dict[title]:
				print("[SYNTAX ERROR] Multiple ingredient blocks with the same name.")
				exit(1)

			if title == 'ingredients':
				recipe_dict[title][subtitle] = []
				for l in body.split("\n"):
					line = l.strip()
					if line != "":

						recipe_dict['ingredient_tags'] = recipe_dict.get('ingredient_tags', []) + [t.strip().lower() for t in re.findall(r"{tag:([^}]*)}", line)]
						recipe_dict['ingredient_tags'] = recipe_dict.get('ingredient_tags', []) + [t.strip().lower() for t in re.findall(r"{alias:[^/]*/([^}]*)}", line)]

						tagged = line.split("*")
						item = tagged[0].strip()

						if len(tagged) > 1:
							tag = tagged[1].strip()
							ingredient_reference[tag] = item

						recipe_dict[title][subtitle].append(item)

			elif title == 'instructions':
				recipe_dict[title][subtitle] = []
				for l in body.split("\n"):
					line = l.strip()
					shorts = re.findall(r"\*([A-Za-z_]*)", line)
					for s in shorts:
						line = line.replace(f"*{s}", ingredient_reference[s])

					recipe_dict[title][subtitle].append(line)
			else:
				recipe_dict[title][subtitle] = body.split("\n")

	file.close()

	return recipe_dict

def writeJSON(recipe_dict):

	ID = recipe_dict['id']
	recipe_json = json.dumps(recipe_dict, indent=4)
	file = open(f"recipe_data/{ID}.json", "w+")
	file.write(recipe_json)
	file.close()

def writeHTML(recipe_dict):

	htmlList = htmlBuilder(recipe_dict)
	HTML = htmlIndenter(htmlList)

	ID = recipe_dict['id']
	file = open(f"pages/{ID}.html", "w+")
	file.write(HTML)
	file.close()

def tagLinkBuilder(m):
	return f'<a href="../index.html?tag={m.group(1).lower()}" style="color: #2c87f0; text-decoration: none">{m.group(1)}</a>'
def aliasLinkBuilder(m):
	return f'<a href="../index.html?tag={m.group(2).lower()}" style="color: #2c87f0; text-decoration: none">{m.group(1)}</a>'

def htmlBuilder(recipe_dict):
	
	html = [
		"<html>",
		"<head>",
		"<link rel=\"stylesheet\" href=\"../main.css\">",
		f"<title>{recipe_dict['title']}</title>",
		"</head>",
		"<body>",
        "<a href=\"../index.html\" class=button>Back</a>"]

	html += [f"<h1>{recipe_dict['title']}</h1>"]

	if 'subtitle' in recipe_dict:
		html += [f"<h2>{recipe_dict['subtitle']}</h2><br>"]

	if 'tags' in recipe_dict:
		tags = ['<p>']
		for tag in recipe_dict['tags']:
			tags.append(f'<a href="../index.html?tag={tag}" class="tags">#{tag}</a>')
		tags.append('</p>')
		html += tags

	if 'batch' in recipe_dict:
		batch = ['<h2>Batch and Time</h2>', '<p class="big-p">']
		batch += [l + "<br>" for l in recipe_dict['batch']['default']]
		batch += ['</p>']
		html += batch

	if 'tools' in recipe_dict:
		tools = ["<h2>Equipment</h2>"]
		for subtitle in recipe_dict['tools']:
			if subtitle != 'default':
				tools.append(f"<h3>{subtitle}</h3>")
			tools.append("<ul>")
			for t in recipe_dict['tools'][subtitle]:
				tools.append(f"<li>{t}</li>")
			tools.append("</ul>")
		html += tools

	if 'ingredients' in recipe_dict:
		ingredients = ["<h2>Ingredients</h2>"]
		for subtitle in recipe_dict['ingredients']:
			if subtitle != 'default':
				ingredients.append(f"<h3>{subtitle}</h3>")
			ingredients.append("<ul>")
			for i in recipe_dict['ingredients'][subtitle]:
				i = re.sub(r"{tag:([^}]*)}", tagLinkBuilder, i)
				i = re.sub(r"{alias:([^/]*)/([^}]*)}", aliasLinkBuilder, i)
				ingredients.append(f"<li>{i}</li>")
			ingredients.append("</ul>")
		html += ingredients
	
	if 'instructions' in recipe_dict:
		instructions = ["<h2>Instructions</h2>"]
		for subtitle in recipe_dict['instructions']:
			if subtitle != 'default':
				instructions.append(f"<h3>{subtitle}</h3>")
			instructions += ["<ol>"]
			for l in recipe_dict['instructions'][subtitle]:
				l = re.sub(r"{tag:([^}]*)}", r"\1", l)
				l = re.sub(r"{alias:([^/]*)/([^}]*)}", r"\1", l)
				instructions.append(f"<li>{l}</li>")
			instructions.append("</ol>")
		html += instructions

	if 'notes' in recipe_dict:
		notes = ["<h2>Notes</h2>"]
		for subtitle in recipe_dict['notes']:
			if subtitle != 'default':
				notes += [f"<h3>{subtitle}</h3>"]
			notes.append("<p>")
			for l in recipe_dict['notes'][subtitle]:
				l = re.sub(r"{link:(.*)}", r'<a href="\1">\1</a>', l)
				notes.append(l + "<br>")
			notes.append("</p>")
		html += notes
	
	html += ["</body>", "</html>"]
	return html

def htmlIndenter(html):

	html_str = "<!DOCTYPE html>\n"

	indent = 0
	for line in html:

		if re.fullmatch("</[^<>]*>", line):
		#	print(line, "indent--")
			indent -= 1

		html_str += indent*"    " + line + "\n"
		if re.fullmatch("<[^/][^<>]*>", line) and line[:5] != '<link':
		#	print(line, "indent++")
			indent += 1
	
	return html_str


if __name__ == '__main__':
	main()