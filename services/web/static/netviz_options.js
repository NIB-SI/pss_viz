
function hover_edge_label(values, id, selected, hovering) {
  values.mod = 'normal';
}

function hover_edge(values, id, selected, hovering) {
  values.width = values.width * 1.5;
}

function hover_node_label(values, id, selected, hovering) {
  values.mod = 'normal';
}

function hover_node(values, id, selected, hovering) {
  values.borderWidth = 5;
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
            edge: hover_edge,
            label: hover_edge_label
        },
        endPointOffset: {
          from: 0,
          to: -5
        },
        arrowStrikethrough: true,
        hoverWidth: 3,
        color: {inherit: false}
    },
    nodes: {
        shape: 'box',
        margin: 10,
        color: {
            border: '#6c7881',
            background: '#9BDBFF'
        },
        widthConstraint: { maximum: 180 },
        font: {
            multi: 'html'
        },
        chosen: {
            node: hover_node,
            label: false,
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
             iterations: 100,
             fit: true
             // updateInterval: 5,
        },
    },
    configure: {
        enabled: false
    },
    layout :{
        randomSeed: 42,
        improvedLayout: true
    }
};