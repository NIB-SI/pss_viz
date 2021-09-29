var network = null;
var node_search_data = null;
var node_search_data_dict = null;
var select = null;


$( document ).ready(function() {
    $.ajax({
      url: "/get_node_data",
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
        var maxlen = 100;
        // console.log(selected_values);
        selected_values.forEach(function (item, index) {
            let node = node_search_data_dict[item];
            let description = node.description.length>0 ? node.description : "/";
            let add_info = node.additional_information.length>0 ? node.additional_information : "/";
            let synonyms = node.synonyms.length>0 ? node.synonyms : "/";

            let list_item = v.vprintf(
                '<a href="#" class="list-group-item list-group-item-action">\
                <div class="d-flex w-100 justify-content-between">\
                <h5 class="mb-1">%s</h5>\
                <button type="button" class="btn btn-link btn-sm float-end"><i class="bi-x-circle" style="color: red;"></i></button>\
                </div>\
                <small><strong>description: </strong>%s</small>\
                <small><strong>synonyms: </strong>%s</small>\
                <small><strong>add. info: </strong>%s</small>\
                <small><strong>id: </strong><div class="node_id">%s</div></small>\
                </a>',
            // [v.truncate(node.name, maxlen),
            //  v.truncate(description,  maxlen - 'description:'.length),
            //  v.truncate(synonyms, maxlen - 'synonyms:'.length),
            //  v.truncate(add_info, maxlen - 'add. info:'.length)
            // ]);
            [node.name,
             description,
             synonyms,
             add_info,
             node.id
            ]);
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
        searchField: ['name', 'synonyms', 'description', 'additional_information'],
        highlight: false,
        render: {
        //   item: function (item, escape) {
        //     return "<div>" + (item.name ? '<span class="name">' + escape(item.name) + "</span>" : "") + (item.description ? '<span class="email">' + escape(item.email) + "</span>" : "") + "</div>";
        // },
          option: function (item, escape) {
            var maxlen = 50;
            // return "<div>" + '<span class="label">' + escape(label) + "</span>" + (caption ? '<span class="caption">' + escape(caption) + "</span>" : "<i>no description available</i>") + "</div>";
            return v.vprintf('<div>\
            <span class="name"> %s </span>\
            <span class="caption"> <strong>description:</strong> %s </span>\
            <span class="caption"> <strong>synonyms:</strong> %s </span>\
            <span class="caption"> <strong>add. info:</strong> %s </span>\
            </div>',
            [v.truncate(escape(item.name), maxlen),
             v.truncate(escape(item.description), maxlen - 'description:'.length),
             v.truncate(escape(item.synonyms), maxlen - 'synonyms:'.length),
             v.truncate(escape(item.additional_information), maxlen - 'add. info:'.length)
            ])
          },
        }
    });

    $('#searchButton').click(function(){
        if($('.node_id').toArray().length==0)
            return;

        $.ajax({
          url: "/search",
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
          url: "/get_network",
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

    scale();
});


function drawNetwork(graphdata){
     var nodes = new vis.DataSet(graphdata.network.nodes);
     // nodes = new vis.DataSet(graphdata.network.nodes);
     var edges = new vis.DataSet(graphdata.network.edges);

     // create a network
     var container = document.getElementById('networkView');

     // provide the data in the vis format
     var data = {
         nodes: nodes,
         edges: edges
     };

     // console.log(data);
     var options = {groups: graphdata.groups,
                    interaction: {hover: true,
                                  navigationButtons: true,
                                  multiselect: true},
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
                        color: {color: 'dimgrey', hover: 'blue'},
                        hoverWidth: 0.6
                        },
                    nodes: {
                        shape: 'box',
                        color: '#9BDBFF',
                        widthConstraint: { maximum: 100},
                        font: {
                            multi: 'html'
                        }
                    },
                    physics: {
                        enabled: true,
                        solver: 'barnesHut',

                        barnesHut: {
                            gravitationalConstant: -5000,
                            centralGravity: 0.5,
                            springLength: 100,
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
    postprocess_edges(data);
    postprocess_nodes(data);
    // var network = new vis.Network(container, data, options);
    network = new vis.Network(container, data, options);
    // network.on("stabilized", function (params) {
    //     network.fit({animation: {duration: 500}});
    //    });
}

function postprocess_edges(data) {
    data.edges.forEach((item, i) => {
        // item.label = item.type;
        // if(item.type == 'binding') {
        //     item.arrows = undefined;
        // }
        // else {
        //     item.arrows = 'to';
        // }

    });
}

function postprocess_nodes(data) {
    data.nodes.forEach((item, i) => {
        let maxlen = 200;
        let title = v.vprintf('<table class="table table-striped table-bordered tooltip_table">\
            <tbody>\
              <tr>\
                <td><strong>Name</strong></td>\
                <td>%s</td>\
              </tr>\
              <tr>\
                <td><strong>Group</strong></td>\
                <td>%s</td>\
              </tr>\
              <tr>\
                <td><strong>Description</strong></td>\
                <td class="text-wrap">%s</td>\
              </tr>\
              <tr>\
                <td><strong>Synonyms</strong></td>\
                <td class="text-wrap">%s</td>\
              </tr>\
              <tr>\
                <td><strong>Add. info</strong></td>\
                <td class="text-wrap">%s</td>\
              </tr>\
            </tbody>\
            </table>', [item.label,
                item.group,
                v.truncate(item.description, maxlen),
                v.truncate(item.synonyms, maxlen),
                v.truncate(item.additional_information, maxlen)]);

        item.title = htmlTitle(title);
    });
}

function htmlTitle(html) {
  const container = document.createElement("div");
  container.classList.add('node_tooltip')
  container.innerHTML = html;
  return container;
}

function scale() {
    $('#networkView').height(verge.viewportH()-10);
    $('#networkView').width($('#networkViewContainer').width());
}
