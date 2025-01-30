<template>
  <div v-if="parsedResults.length">
    <table class="pingall-table">
      <thead>
        <tr>
          <th v-for="header in headers" :key="header">{{ header }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in parsedResults" :key="index">
          <td v-for="(value, key) in row" :key="key">{{ value }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div v-else>
    <p>No ping results available.</p>
  </div>
</template>

<script>
export default {
  props: {
    pingResults: {
      type: String,
      required: true
    }
  },
  computed: {
    headers() {
      return ["src", "dst", "packets_sent", "packets_recv", "min", "avg", "max", "mdev"];
    },
    parsedResults() {
      if (!this.pingResults) return [];

      const cleanedData = this.pingResults
        .replaceAll("min/avg/max/mdev", "")
        .replaceAll("/", " ")
        .replaceAll("->", " ")
        .replaceAll(",", "")
        .replaceAll(":", "")
        .replaceAll("rtt", "")
        .split(/\s+/)
        .filter(Boolean);

      const rows = [];
      for (let i = 0; i < cleanedData.length; i += 9) {
        const row = {
          src: cleanedData[i],
          dst: cleanedData[i + 1],
          packets_sent: cleanedData[i + 2],
          packets_recv: cleanedData[i + 3],
          min: cleanedData[i + 4],
          avg: cleanedData[i + 5],
          max: cleanedData[i + 6],
          mdev: cleanedData[i + 7]
        };
        rows.push(row);
      }

      return rows;
    }
  }
};
</script>

<style scoped>
.pingall-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.pingall-table th, .pingall-table td {
  border: 1px solid #ddd;
  padding: 8px;
}

.pingall-table th {
  background-color: #f2f2f2;
}
</style>
