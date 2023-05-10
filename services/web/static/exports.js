

function format_cell(s){
    s = s.toString();
    s = s.trim();
    s = s.replace('\n', ' ');
    s = s.replace(/<\/?[^>]+(>|$)/g, "");
    return s;
}

function export_nodes() {
    if(netviz.nodes==undefined) {
        vex.dialog.alert('No nodes to export! You need to do a search first.');
        return;
    }

    var data = [NODE_ANNOT_DATA];
    netviz.nodes.forEach(function(node, id){
        var line = new Array;

        NODE_ANNOT_DATA.forEach(function(aname){
            let atr = node[aname];
            if (atr != undefined)
                line.push(format_cell(atr));
            else
                line.push('');
        })
        SPECIES.forEach(function(sp){
            let atr = node['_homologues'][sp];
            if (atr != undefined)
                line.push(format_cell(atr));
            else
                line.push('');
        })
        data.push(line);
    })

    var datalines = new Array;
    data.forEach(function(line_elements){
        datalines.push(line_elements.join('\t'));
    })
    var csv = datalines.join('\n')

    var blob = new Blob([csv], {type: "text/csv;charset=utf-8"});
    saveAs(blob, "nodes.tsv");
}

function export_edges(){
    if(netviz.edges==undefined) {
        vex.dialog.alert('No edges to export! You need to do a search first.');
        return;
    }


    var data = [['from','to','label']];
    netviz.edges.forEach(function(edge, id){
        var line = new Array;

        ['from','to','label'].forEach(function(aname){
            let atr = edge[aname];
            if (atr != undefined)
                line.push(format_cell(atr));
            else
                line.push('');
        })

        data.push(line);
    })

    var datalines = new Array;
    data.forEach(function(line_elements){
        datalines.push(line_elements.join('\t'));
    })
    var csv = datalines.join('\n');

    var blob = new Blob([csv], {type: "text/csv;charset=utf-8"});
    saveAs(blob, "edges.tsv");
}


function export_png(){
    if(netviz.nodes==undefined) {
        vex.dialog.alert('No image to export! You need to do a search first.');
        return;
    }

    const ctx = netviz.network.canvas.getContext()
    const dataURL = ctx.canvas.toDataURL('image/png');

    saveAs(dataURL, "network.png");
}

function export_json(){
    if(netviz.nodes==undefined) {
        vex.dialog.alert('No network to export! You need to do a search first.');
        return;
    }

    json_nodes = []
    json_edges = []

    coords = netviz.network.getPositions()

    netviz.nodes.forEach(function(node, id){
        var data = {};

        NODE_ANNOT_DATA.forEach(function(aname){
            let atr = node[aname];
            if ((atr != undefined) && (atr != "")) {
                data[aname] = format_cell(atr);
            }
        })
        SPECIES.forEach(function(sp){
            let atr = node['_homologues'][sp];
            if (atr != undefined){
                data['{}_homologues'.format(sp)] = format_cell(atr);
            }
        })
        // console.log(line)

        json_nodes.push({"data":data, "position":coords[id], "group": "nodes"});
    })

    netviz.edges.forEach(function(edge, id){

        var data = {};
        data["source"] = edge["from"];
        data["target"] = edge["to"];
        data["label"] = edge["label"];

        json_edges.push({"data":data, "group": "edges"});
    })


    json = JSON.stringify({"elements":
        {
            "nodes": json_nodes,
            "edges": json_edges
        }
    })

    var blob = new Blob([json], {type: "application/json"});
    saveAs(blob, "network.json");
}