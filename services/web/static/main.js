// prevents dialog closing immediately when page navigates
vex.defaultOptions.closeAllOnPopState = false;

var netviz = {
    nodes: undefined,
    edges: undefined,
    network: undefined,
    isFrozen: false,
    newNodes: undefined,
    newEdges: undefined
};


// var network = null;
var node_search_data = null;
var node_search_data_dict = null;
var select = null;

format.extend (String.prototype, {});

$(window).resize(function() {
    scale();
});

$( document ).ready(function() {

    $.ajax({
      url: "/biomine/get_node_data",
      async: false,
      dataType: 'json',
      type: "POST",
      contentType: 'application/json; charset=utf-8',
      processData: false,
      success: function( data, textStatus, jQxhr ){
          // console.log(data.node_data);
          node_search_data = data.node_data;
          node_search_data_dict = Object.assign({}, ...node_search_data.map((x) => ({[x.id]: x})));
      },
      error: function( jqXhr, textStatus, errorThrown ){
          alert('Server error while loading node data.');
      }
    });

    $('#add2selected').click(function(){
        var selected_values = select[0].selectize.getValue();
        // var maxlen = 100;
        // console.log(selected_values);
        selected_values.forEach(function (item, index) {
            let node = node_search_data_dict[item];
            let nodeName = v.truncate(node.name, 25);
            let functional_cluster_id = node.functional_cluster_id.length>0 ? '<small><strong>fc identifier: </strong>{}</small>'.format(node.functional_cluster_id) : "";
            let description = node.description.length>0 ? '<small><strong>description: </strong>{}</small>'.format(node.description) : "";
            let synonyms = node.synonyms.length>0 ? '<small><strong>synonyms: </strong>{}</small>'.format(node.synonyms) : "";
            let evidence_sentence = node.evidence_sentence.length>0 ? '<small><strong>evidence: </strong>{}</small>'.format(node.evidence_sentence) : "";
            let node_id = '<small style="font-size:0px;"><strong>id: </strong><div class="node_id">{}</div></small>'.format(node.id);

            let list_item = '<a href="#" class="list-group-item list-group-item-action">\
                <div class="d-flex w-100 justify-content-between">\
                <h5 class="mb-1">{}</h5>\
                <button type="button" class="btn btn-link btn-sm float-end"><i class="bi-x-circle" style="color: red;"></i></button>\
                </div>\
                {}\
                {}\
                {}\
                {}\
                {}\
                </a>'.format(nodeName, functional_cluster_id, description, synonyms, evidence_sentence, node_id);

         $('#queryList').append(list_item);
         // scroll to bottom
         let element = $('#queryList')[0];
         element.scrollTop = element.scrollHeight;

         select[0].selectize.clear();
         $(".list-group-item button").click(function(){
           $(this).parent().parent().remove();
         })

        });
    });

    select = $('#queryInput').selectize({
        options: node_search_data,
        maxItems: null,
        closeAfterSelect: true,
        valueField: "id",
        labelField: "name",
        sortField: "name",
        searchField: ['name', 'synonyms', 'description', 'evidence_sentence', 'functional_cluster_id'],
        highlight: false,
        render: {
        //   item: function (item, escape) {
        //     return "<div>" + (item.name ? '<span class="name">' + escape(item.name) + "</span>" : "") + (item.description ? '<span class="email">' + escape(item.email) + "</span>" : "") + "</div>";
        // },
          option: function (item, escape) {
            let maxlen = 50;
            let name = '<span class="name"> {} </span>'.format(v.truncate(escape(item.name), maxlen));
            let functional_cluster_id = item.functional_cluster_id.length>0 ? '<small><strong>fc identifier: </strong>{}</small>'.format(item.functional_cluster_id) : "";
            let description = item.description.length>0 ? '<span class="caption"> <strong>description:</strong> {} </span>'.format(v.truncate(escape(item.description), maxlen - 'description:'.length)) : "";
            let synonyms = item.synonyms.length>0 ? '<span class="caption"> <strong>synonyms:</strong> {} </span>'.format(v.truncate(escape(item.synonyms), maxlen - 'synonyms:'.length)) : "";
            let evidence_sentence = item.evidence_sentence.length>0 ? '<span class="caption"> <strong>evidence:</strong> {} </span>'.format(v.truncate(escape(item.evidence_sentence), maxlen - 'evidence:'.length)) : "";

            return '<div>\
            {}\
            {}\
            {}\
            {}\
            {}\
            </div>'.format(name, functional_cluster_id, description, synonyms, evidence_sentence);
          },
        }
    });

    $('#searchButton').click(function(){
        if($('.node_id').toArray().length==0)
            return;

        $.ajax({
          url: "/biomine/search",
          dataType: 'json',
          type: "POST",
          contentType: 'application/json; charset=utf-8',
          processData: false,
          data: JSON.stringify({'nodes': $('.node_id').toArray().map(x => $(x).text())}),
          success: function( data, textStatus, jQxhr ){
              // console.log(data);
              drawNetwork(data);
              // console.log(data.network);
              // $('#response pre').html( JSON.stringify( data ) );
          },
          error: function( jqXhr, textStatus, errorThrown ){
              alert('Server error while loading the network.');
          }
        });
    });


    $('#draw_complete_network_button').click(function(){
        $.ajax({
          url: "/biomine/get_network",
          dataType: 'json',
          type: "GET",
          contentType: 'application/json; charset=utf-8',
          success: function( data, textStatus, jQxhr ){
              drawNetwork(data);
              // console.log(data.network);
              // $('#response pre').html( JSON.stringify( data ) );
          },
          error: function( jqXhr, textStatus, errorThrown ){
              alert('Server error while loading the network.');
          }
        });
    });

    $("#showTooltipsCbox").change(function() {
        if (netviz.network) {
            if (this.checked) {
                netviz.network.setOptions({interaction:{tooltipDelay:200}});
            }
            else {
                netviz.network.setOptions({interaction:{tooltipDelay:3600000}});
            }
        }
    });
    $("#showTooltipsCbox").prop("checked", false);

    scale();
    initContextMenus();

    urlParams = new URLSearchParams(window.location.search);
    reaction_list = urlParams.getAll('reaction_id');
    console.log(reaction_list);
    functional_cluster_list = urlParams.getAll('functional_cluster_id');
    console.log(functional_cluster_list);

    if(reaction_list.length>0){
        console.log("here")
        for (var i = reaction_list.length - 1; i >= 0; i--) {
            rx = reaction_list[i]
            console.log(rx);

            var j = -1
            for (let x of node_search_data) {
               if (x.name == rx){
                console.log(x.id);
                j = x.id;
                break;
               }
            }
            if (j == -1){
                alert(rx + ' is not a valid reaction_id' )
            } else {
                select[0].selectize.addItem(j);
                $('#add2selected').click()
            }
        }
    }
    if(functional_cluster_list.length>0){
        console.log("here")
        for (var i = functional_cluster_list.length - 1; i >= 0; i--) {
            fc = functional_cluster_list[i]
            console.log(fc);

            var j = -1
            for (let x of node_search_data) {
               if (x.functional_cluster_id == fc){
                console.log(x.id);
                j = x.id;
                break;
               }
            }
            if (j == -1){
                alert(fc + ' is not a valid functional_cluster_id' )
            } else {
                select[0].selectize.addItem(j);
                $('#add2selected').click()
            }
        }
    }
    $('#searchButton').click();



    $('#saveAsDropdown a').click(function(){
        if ($(this).attr('href') == '#nodes') {
            export_nodes();
        }
        else if ($(this).attr('href') == '#edges') {
            export_edges();
        }
    });

});


function drawNetwork(graphdata){
     netviz.nodes = new vis.DataSet(graphdata.network.nodes);
     netviz.edges = new vis.DataSet(graphdata.network.edges);

     // create a network
     var container = document.getElementById('networkView');

     // provide the data in the vis format
     var data = {
         nodes: netviz.nodes,
         edges: netviz.edges
     };

     // console.log(data);
     var options = {groups: graphdata.groups,
                    interaction: {hover: true,
                                  navigationButtons: true,
                                  multiselect: true,
                                  tooltipDelay: $("#showTooltipsCbox").prop("checked") ? 200 : 3600000,  // effectively disabled by very long delay if unchecked
                                },
                    edges: {
                        arrows: 'to',
                        smooth: {
                            enabled: true,
                            // type: 'continuous'
                            type: 'dynamic',
                            forceDirection: 'none'
                        },
                        font: {
                            size: 9,
                            face: 'sans',
                            align: 'top', //'middle'
                            color: '#808080'
                        },
                        chosen: {
                            label: hover_edge_label
                        },
                        color: {color: 'dimgrey', hover: 'blue'},
                        hoverWidth: 0.6
                        },
                    nodes: {
                        shape: 'box',
                        color: '#9BDBFF',
                        widthConstraint: { maximum: 100},
                        font: {
                            multi: 'html'
                        },
                        chosen: {
                            node: hover_node,
                            label: hover_node_label
                        }
                    },
                    physics: {
                        enabled: true,
                        solver: 'barnesHut',

                        barnesHut: {
                            gravitationalConstant: -5000,
                            centralGravity: 0.5,
                            springLength: 150,
                            springConstant: 0.16,
                            damping: 0.25
                        },
                        stabilization: {
                             enabled: true,
                             iterations: 10,
                             fit: true
                             // updateInterval: 5,
                         },
                    },
                    configure: {
                        enabled: false
                    },
                    layout :{
                        improvedLayout: true
                    }
    };
    postprocess_edges(data.edges);
    postprocess_nodes(data.nodes);
    // var network = new vis.Network(container, data, options);
    netviz.network = new vis.Network(container, data, options);
    netviz.network.on('dragStart', onDragStart);
    netviz.network.on('dragEnd', onDragEnd);

    // network.on("stabilized", function (params) {
    //     network.fit({animation: {duration: 500}});
    //    });
}

function hover_edge_label(values, id, selected, hovering) {
  values.mod = 'normal';
}

function hover_node_label(values, id, selected, hovering) {
  values.mod = 'normal';
}

function hover_node(values, id, selected, hovering) {
  values.borderWidth = 2;
  values.borderColor = 'blue'
  // values.color = 'blue'
}

function postprocess_edges(edges) {
    edges.forEach((item, i) => {
        // item.label = item.type;
        // if(item.type == 'binding') {
        //     item.arrows = undefined;
        // }
        // else {
        //     item.arrows = 'to';
        // }

    });
}

function postprocess_node(item) {
    let maxlen = 100;
    let header = '<table class="table table-striped table-bordered tooltip_table w-100" style="table-layout: fixed;">\
                  <tbody>';
    let footer = '</tbody>\
                  </table>';
    let data = [['Name', item.label],
                ['Group', item.group],
                ['Reaction type', item.reaction_type],
                ['FunctionalCluster id', item.functional_cluster_id],
                ['Description', v.truncate(item.description, maxlen)],
                ['Synonyms', v.truncate(item.synonyms, maxlen)],
                ['Evidence', v.truncate(item.evidence_sentence, maxlen)],
                ['External links:', item.external_links]];

    for (let sp in item._homologues) {
        s = v.truncate(item._homologues[sp], maxlen)
        if (sp=="ath") {
            params = jQuery.param({list:item._homologues[sp]})
            s += '<p><a target="_blank" href="https://knetminer.com/araknet/genepage?{}">Search for {}_homologues in KnetMiner</a></p>'.format(params, sp)
        }
        data.push(['{}_homologues'.format(sp), s])
    }

    let table = '';
    data.forEach(function (item, index) {
        if (item[1].length>0) {
            let row = '<tr>\
                            <td><strong>{}</strong></td>\
                            <td class="text-wrap" style="width: 100%; display: inline-block; word-wrap: break-word; ">{}</td>\
                       </tr>'.format(item[0], item[1]);
            table += row;
        }
    });
    table = header + table + footer;
    item.title = htmlTitle(table);
    return item;
}

function postprocess_nodes(nodes) {
    nodes.forEach((item, i) => {
        // console.log('postproceesing ' + item.label);
        nodes[i] = postprocess_node(item);
    });
}

function htmlTitle(html) {
  const container = document.createElement("div");
  container.classList.add('node_tooltip')
  container.innerHTML = html;
  return container;
}

function scale() {
    $('#networkView').height(verge.viewportH()-80);
    $('#networkView').width($('#networkViewContainer').width());
}

function freezeNodes(state){
    netviz.network.stopSimulation();
    netviz.nodes.forEach(function(node, id){
        netviz.nodes.update({id: id, fixed: state});
    });
    netviz.network.startSimulation();
}

function onDragStart(obj) {
    if (obj.hasOwnProperty('nodes') && obj.nodes.length==1) {
        var nid = obj.nodes[0];
        netviz.nodes.update({id: nid, fixed: false});
    }

}

function onDragEnd(obj) {
    if (netviz.isFrozen==false)
        return
    var nid = obj.nodes;
    if (obj.hasOwnProperty('nodes') && obj.nodes.length==1) {
        var nid = obj.nodes[0];
        netviz.nodes.update({id: nid, fixed: true});
    }
}

function formatNodeInfoVex(nid) {
    return netviz.nodes.get(nid).title;
}

function edge_present(edges, newEdge) {
    var is_present = false;
    var BreakException = {};

    try {
        edges.forEach((oldEdge, i) => {
            if (newEdge.from == oldEdge.from &&
                newEdge.to == oldEdge.to &&
                newEdge.label == oldEdge.label) {
                    is_present = true;
                    throw BreakException; // break is not available in forEach
                }
        })
    } catch (e) {
        if (e !== BreakException) throw e;
    }
    return is_present;
}

function expandNode(nid) {
    $.ajax({
      url: "/biomine/expand",
      async: false,
      dataType: 'json',
      type: "POST",
      contentType: 'application/json; charset=utf-8',
      processData: false,
      data: JSON.stringify({'nodes': [nid]}),
      success: function( data, textStatus, jQxhr ){
          if (data.error) {
              vex.dialog.alert('Server error when expanding the node. Please report the incident.')
          }
          else {
              let newCounter = 0
              data.network.nodes.forEach((item, i) => {
                  if (!netviz.nodes.get(item.id)) {
                      netviz.nodes.add(postprocess_node(item));
                      newCounter += 1;
                  }
                  else {
                      // console.log('Already present ' + item.id + item.label)
                  }
              })

              data.network.edges.forEach((newEdge, i) => {
                  if(!edge_present(netviz.edges, newEdge)) {
                      netviz.edges.add(newEdge);
                      newCounter += 1;
                  }
              })

              data.network.potential_edges.forEach((edge, i) => {
                  if(!edge_present(netviz.edges, edge)) {
                      netviz.edges.add(edge);
                      newCounter += 1;
                  }
              })

              if (newCounter==0) {
                  vex.dialog.alert('No nodes or edges can be added.');
              }
          }
      },
      error: function( jqXhr, textStatus, errorThrown ){
          alert('Server error while loading node data.');
      }
    });

}


function initContextMenus() {
    var canvasMenu = {
        "stop": {name: "Stop simulation"},
        "start" : {name: "Start simulation"}
    };
    var canvasMenu = {
        "freeze": {name: "Freeze positions"},
        // "release" : {name: "Start simulation"}
    };
    var nodeMenuFix = {
        "delete": {name: "Delete"},
        "expand": {name: "Expand"},
        "fix": {name: "Fix position"},
        "info": {name: "Info"}
    };
    var nodeMenuRelease = {
        "delete": {name: "Delete"},
        "expand": {name: "Expand"},
        "release": {name: "Release position"},
        "info": {name: "Info"}
    };
    var edgeMenu = {
        "delete": {name: "Delete"},
        // "info": {name: "Info"}
    };

    $.contextMenu({
            selector: 'canvas',
            build: function($trigger, e) {
                // this callback is executed every time the menu is to be shown
                // its results are destroyed every time the menu is hidden
                // e is the original contextmenu event, containing e.pageX and e.pageY (amongst other data)

                var hoveredEdge = undefined;
                var hoveredNode = undefined;
                if (!$.isEmptyObject(netviz.network.selectionHandler.hoverObj.nodes)) {
                    hoveredNode = netviz.network.selectionHandler.hoverObj.nodes[Object.keys(netviz.network.selectionHandler.hoverObj.nodes)[0]];
                }
                else {
                    hoveredNode = undefined;
                }
                if (!$.isEmptyObject(netviz.network.selectionHandler.hoverObj.edges)) {
                    hoveredEdge = netviz.network.selectionHandler.hoverObj.edges[Object.keys(netviz.network.selectionHandler.hoverObj.edges)[0]];
                }
                else {
                    hoveredEdge = undefined;
                }

                // ignore auto-highlighted edge(s) on node hover
                if (hoveredNode != undefined && hoveredEdge != undefined)
                    hoveredEdge = undefined;

                if (hoveredNode != undefined && hoveredEdge == undefined) {
                    return {
                        callback: function(key, options) {
                            if (key == "delete") {
                                netviz.nodes.remove(hoveredNode);
                            }
                            else if (key == "expand") {
                                expandNode(hoveredNode.id);
                                // vex.dialog.alert("Not yet implemented.");
                            }
                            else if (key == "fix") {
                                netviz.nodes.update({id: hoveredNode.id, fixed: true});
                            }
                            else if (key == "release") {
                                netviz.nodes.update({id: hoveredNode.id, fixed: false});
                            }
                            else if (key == "info") {
                                vex.dialog.alert({unsafeMessage: formatNodeInfoVex(hoveredNode.id)});
                            }
                        },
                        items: netviz.nodes.get(hoveredNode.id).fixed ? nodeMenuRelease : nodeMenuFix
                    };
                }
                else if (hoveredNode == undefined && hoveredEdge != undefined) {
                    return {
                        callback: function(key, options) {
                            if (key == "delete") {
                                netviz.edges.remove(hoveredEdge);
                            }
                            else if (key == "info") {
                                vex.dialog.alert({unsafeMessage: formatEdgeInfoVex(hoveredEdge.id)});
                            }
                        },
                        items: edgeMenu
                    };
                }
                else {
                    if (netviz.isFrozen) {
                        canvasMenu.freeze.name = "Release positions";
                        return {
                            callback: function(key, options) {
                                if (key == "freeze") {
                                    netviz.isFrozen = false;
                                    freezeNodes(netviz.isFrozen);
                                }
                            },
                            items: canvasMenu
                        };
                    }
                    else {
                        canvasMenu.freeze.name = "Freeze positions";
                        return {
                            callback: function(key, options) {
                                if (key == "freeze") {
                                    netviz.isFrozen = true;
                                    freezeNodes(netviz.isFrozen);
                                }
                            },
                            items: canvasMenu
                        };
                    }
                }
            }
        });

}


function format_cell(s){
    s = s.toString();
    s = s.trim();
    s = s.replace('\n', '');
    if (s[0]!='"' && s.slice(-1)!='"' && s.search(',')!=-1){
        s = '"' + s + '"';
    }
    return s;
}



function export_nodes() {
    if(netviz.nodes==undefined) {
        vex.dialog.alert('No nodes to export! You need to do a search first.');
        return;
    }

    // for (let sp in item._homologues) {
    //     s = v.truncate(item._homologues[sp], maxlen)
    //     data.push(['{}_homologues'.format(sp), s])
    // }


    var data = [['id', 'label','group','description','synonyms','evidence sentence','external links','reaction type', 'functional_cluster_id', 'homologues']];
    netviz.nodes.forEach(function(node, id){
        var line = new Array;

        ['id', 'label','group','description','synonyms','evidence_sentence', 'external_links','reaction_type', 'functional_cluster_id', '_homologues'].forEach(function(aname){
            let atr = node[aname];
            if (atr != undefined)
                line.push(format_cell(atr));
            else
                line.push('');
        })
        data.push(line);
    })

    var datalines = new Array;
    data.forEach(function(line_elements){
        datalines.push(line_elements.join(','));
    })
    var csv = datalines.join('\n')

    var blob = new Blob([csv], {type: "text/csv;charset=utf-8"});
    saveAs(blob, "nodes.csv");
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
        datalines.push(line_elements.join(','));
    })
    var csv = datalines.join('\n');

    var blob = new Blob([csv], {type: "text/csv;charset=utf-8"});
    saveAs(blob, "edges.csv");
}

