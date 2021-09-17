var network_data = null;

$( document ).ready(function() {
    $.ajax({
      url: "/get_network",
      dataType: 'json',
      type: "POST",
      // contentType: 'application/json; charset=utf-8',
      processData: false,
      success: function( data, textStatus, jQxhr ){
          network_data = data;
          drawNetwork(data.network);
          // console.log(data.network);
          // $('#response pre').html( JSON.stringify( data ) );
      },
      error: function( jqXhr, textStatus, errorThrown ){
          alert('Server error while loading the network.');
      }
    });
    scale();
});


function drawNetwork(data){
     var nodes = new vis.DataSet(data.nodes);
     var edges = new vis.DataSet(data.edges);

     // create a network
     var container = document.getElementById('networkView');

     // provide the data in the vis format
     var data = {
         nodes: nodes,
         edges: edges
     };

     var options = {interaction: {hover: true,
                                  navigationButtons: true,
                                  multiselect: true},
                    edges: {
                        // arrows: 'to',
                        smooth: {
                            enabled: true,
                            //type: 'continuous'
                            type: 'dynamic',
                            forceDirection: 'none'
                        },
                        font: {
                            size: 9,
                            face: 'sans',
                            align: 'horizontal',
                            color: '#808080'
                        },
                        color: {color: 'dimgrey', hover: 'blue'},
                        hoverWidth: 0.6,
                        },
                    nodes: {
                        shape: 'box',
                        color: '#9BDBFF'
                    },
                    physics: {
                        enabled: false,
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
                             // updateInterval: 5,
                             fit: true
                         },
                    },
                    configure: {
                        enabled: false
                    }


    };
    postprocess_edges(data);
    postprocess_nodes(data);
    var network = new vis.Network(container, data, options);
    network.on("stabilized", function (params) {
        network.fit({animation: {duration: 500}});
       });
}

function postprocess_edges(data) {
    data.edges.forEach((item, i) => {
        item.label = item.type;
        if(item.type == 'binding') {
            item.arrows = undefined;
        }
        else {
            item.arrows = 'to';
        }

    });
}

function postprocess_nodes(data) {
    // data.nodes.forEach((item, i) => {
    // });
}


function scale() {
    $('#networkView').height(verge.viewportH()-10);
    $('#networkView').width($('#networkViewContainer').width());
}
