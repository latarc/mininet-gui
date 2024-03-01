
export const options = {
  // clickToUse: true,
  // configure: {
  //   enabled: true,
  //   filter: 'nodes,edges',
  //   showButton: true
  // },
  edges: {
    width: 5,
    color: {
      color: "#848484",
      highlight: "#848484",
      hover: "#848484",
      inherit: "from",
      opacity: 1.0,
    },
    smooth: false,
  },
  nodes: {
    shape: "box",
    margin: 10,
    widthConstraint: {
      maximum: 200,
    },
  },
  interaction: {
    keyboard: true,
    multiselect: true,
  },
  physics: {
    enabled: false,
  },
};
