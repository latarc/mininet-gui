export const buildOptions = (theme = "dark") => {
  const isLight = theme === "light";
  const edgeColor = isLight ? "#7a7a7a" : "#848484";
  const nodeBackground = isLight ? "#f3f3f3" : "#252526";
  const nodeHighlight = isLight ? "#bdbdbd" : "#848484";
  const fontColor = isLight ? "#2b2b2b" : "#cccccc";
  return {
    edges: {
      width: 5,
      color: {
        color: edgeColor,
        highlight: edgeColor,
        hover: edgeColor,
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
        color: fontColor,
        size: 14,
        face: "Fira Sans",
      },
      color: {
        border: "#00000000",
        background: nodeBackground,
        highlight: {
          border: nodeHighlight,
          background: nodeHighlight,
        },
        hover: {
          border: nodeHighlight,
          background: nodeHighlight,
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
};

export const options = buildOptions("dark");
