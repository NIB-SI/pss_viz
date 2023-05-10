
function hover_edge_label(values, id, selected, hovering) {
  values.mod = 'normal';
}

function hover_node_label(values, id, selected, hovering) {
  values.mod = 'normal';
}

function hover_node(values, id, selected, hovering) {
  values.borderWidth = 4;
  // values.borderColor = 'blue'
  // values.color = 'blue'
}

var netviz_options = {
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
        endPointOffset: {
          from: 0,
          to: -5
        },
        arrowStrikethrough: true,
        hoverWidth: 2
    },
    nodes: {
        shape: 'box',
        margin: 10,
        color: {
            border: '#6c7881',
            background: '#9BDBFF'
        },
        widthConstraint: { maximum: 180},
        font: {
            multi: 'html'
        },
        chosen: {
            node: hover_node,
            label: hover_node_label,
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