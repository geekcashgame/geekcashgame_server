import json

data = {
	"name":"fredshao",
	"age":27,
	"score":99,
}

json_str = json.dumps(data)

with open("data.json", "w", encoding="utf-8") as f:
	f.write(json_str)