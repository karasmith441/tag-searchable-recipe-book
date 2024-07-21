// ======================== Globals ========================

var inpt = document.getElementById("searchbar");


// ======================= Functions =======================

// function getUrlParams() {

//   var paramMap = {};
//   if (location.search.length == 0) {
//     return paramMap;
//   }
//   var parts = location.search.substring(1).split("&");

//   for (var i = 0; i < parts.length; i ++) {
//     var component = parts[i].split("=");
//     paramMap[decodeURIComponent(component[0])] = decodeURIComponent(component[1]);
//   }
//   return paramMap;
// }

// tag_inpt = getUrlParams()['tag'];
// if(tag_inpt != null){
// 	inpt.value = tag_inpt;
// }

function clearSearch()
{
	inpt.value = "";
	window.location.href = "index.html";
	readBase();
}

function readBase()
{
	sessionStorage.setItem('search', inpt.value);
	fetch("rpbase.json").then((response) => response.json()).then((json) => generateLinks(json));
}

function evalSearchbar(tags, otags, search)
{
	let tag_bools = [];
	let tag_ops = [];
	let tag = ""
	let recursive_flag = false;
	for(let i = 0; i < search.length; i++)
	{
		let c = search[i];
		if(c == "(")
		{
			let recursive_bool = evalSearchbar(tags, search.slice(i+1));
			if(tag.trim() == "!")
			{
				recursive_bool = !recursive_bool;
			}
			tag_bools.push(recursive_bool);
			while(search[i] != ")" && i < search.length)
			{
				i++;
			}
			recursive_flag = true;
		}
		else if(c == ")")
		{
			i = search.length;
		}
		else if(c == "+" || c == "&" || c == "|" || c == "/")
		{
			if(!recursive_flag)
			{
				if(tag.trim()[0] == "!")
				{
					tag_bools.push(tags.indexOf(tag.trim().slice(1)) < 0);
				}
				else
				{
					tag_bools.push(tags.indexOf(tag.trim()) >= 0 || otags.indexOf(tag.trim()) >= 0);
				}
			}
			tag = "";
			recursive_flag = false;
			if(c == "+" || c == "&")
			{
				tag_ops.push("&");
			}
			else if(c == "|" || c == "/")
			{
				tag_ops.push("|");
			}
		}
		else if(c == "#")
		{}
		else
		{
			tag += c;
		}
	}

	if(tag.trim()[0] == "!" || tag.trim()[0] == "-")
	{
		tag_bools.push(tags.indexOf(tag.trim().slice(1)) < 0);
	}
	else
	{
		tag_bools.push(tags.indexOf(tag.trim()) >= 0 || otags.indexOf(tag.trim()) >= 0);
	}

	bool = tag_bools[0];
	for(let i = 0; i < tag_ops.length; i++)
	{
		op = tag_ops[i];
		switch(op)
		{
			case "&":
				bool &= tag_bools[i+1];
				break;
			case "|":
				bool |= tag_bools[i+1];
				break;
		}
	}

	return bool;
}

function generateLinks(json)
{
	document.getElementById("links").innerHTML = "";
	query = inpt.value.trim();

	for(const [k, v] of Object.entries(json))
	{
		flag = true;
		if(query != "")
		{
			flag = evalSearchbar(v["tags"], v["otags"], query);
		}
		if(flag)
		{
			document.getElementById("links").innerHTML += "<a href=\"pages/" + k + ".html\" class=\"big-link\">" + v["name"] + "</a><br><br>";
		}
	}
}

// ======================== Main ========================

if (location.search.length != 0) {
	inpt.value = decodeURIComponent(location.search.substring(5)).replace(/\+/g, "&");
}
readBase();
inpt.addEventListener("keyup", function(event) {
	if (event.key === "Enter"){
		readBase();
	}
});
