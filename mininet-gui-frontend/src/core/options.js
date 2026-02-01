export const options = {
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
    margin: 10,
    widthConstraint: {
      maximum: 200,
    },
    font: {
      color: "#cccccc",
      size: 14,
      face: "Fira Sans",
    },
    color: {
      border: "#00000000",
      background: "#252526",
      highlight: {
        border: "#848484",
        background: "#848484",
      },
      hover: {
        border: "#848484",
        background: "#848484",
      },
    },
  },
  interaction: {
    keyboard: true,
    multiselect: true,
    dragView: false,
  },
  physics: {
    enabled: false,
  },
};
