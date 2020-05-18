var chart;

function requestData() {
  // Ajax call to get the Data from Flask
  var requests = $.get('/data');

  var tm = requests.done(function(result) {
    // Temperature
    var series = chart.series[0],
      shift = series.data.length > 20;

    // Humidity
    // Add the Point
    // Time Temperature\
    var data1 = [];
    data1.push(result[0]);
    data1.push(result[1]);

    chart.series[0].addPoint(data1, true, shift);

    $(".ltp").text("");
    $(".ltp").text(Math.round(data1[1]));

    if (result[2] > 0) {
      $(".change").text("");
      $(".change").text(" +" + Math.round(result[2]));
      $(".change").css("color", "green")

      $(".change_p").text("");
      $(".change_p").text("(+" + Math.round(result[3]) + "%)");
      $(".change_p").css("color", "green")
    } else if (result[2] < 0) {
      $(".change").text("");
      $(".change").text(" -" + Math.round(result[2]));
      $(".change").css("color", "red")

      $(".change_p").text("");
      $(".change_p").text("(-" + Math.round(result[3]) + "%)");
      $(".change_p").css("color", "red")
    } else {
      $(".change").text("");
      $(".change").text(Math.round(result[2]));


      $(".change_p").text("");
      $(".change_p").text(Math.round(result[3]) + "%)");

    }

    $(".last_traded").text("");
    $(".last_traded").text("Last traded on " + result[4]);

    // call it again after one second
    setTimeout(requestData, 2000);

  });
}

$(document).ready(function() {
  // --------------Chart 1 ----------------------------
  chart = new Highcharts.Chart({
    chart: {
      renderTo: 'data-container',
      defaultSeriesType: 'area',
      zoomType: 'x',
      panning: true,
      panKey: 'shift',
      events: {
        load: requestData
      }
    },
    time: {
      useUTC: false
    },
    title: {
      text: "{{token}}"
    },
    subtitle: {
      text: 'Click and drag to zoom in. Hold down shift key to pan.'
    },
    xAxis: {
      type: 'datetime',
      tickPixelInterval: 150,
      maxZoom: 20 * 1000
    },
    yAxis: {
      minPadding: 0.1,
      maxPadding: 0.1,
      title: {
        text: 'LTP',
        margin: 20
      }
    },
    series: [{
      color: '#d65a31',
      lineColor: '#393e46',
      name: 'LTP of {{ticker}}',
      data: []
    }]
  });
});

// --------------Chart 1 Ends - -----------------


function ddselect() {
  var d = document.getElementById("inputGroupSelect01");
  var type = d.options[d.selectedIndex].text;
  var null_value = "NULL"
  if (type.localeCompare("MRKT") == 0) {
    document.getElementById("price").value = null_value;
    document.getElementById("price").setAttribute('readonly', true);
  }

  if (type.localeCompare("LMT") == 0) {
    document.getElementById("price").removeAttribute('readonly');
  }

}
