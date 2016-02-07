document.addEventListener('DOMContentLoaded', function() {
  var uptownEstimate = document.getElementById('uptown-estimate');
  var downtownEstimate = document.getElementById('downtown-estimate');

  function getData(callback) {
    var request = new XMLHttpRequest();

    request.onreadystatechange = function() {
      if (request.readyState === 4) {
        callback(request);
      }
    };

    request.open('GET', '/estimates', true);
    request.send();
  }

  function pollServer() {
    getData(function(response) {
      var responseData = JSON.parse(response.responseText);

      if (responseData.status === 'success') {
        uptownEstimate.innerText = responseData.data.uptown;
        downtownEstimate.innerText = responseData.data.downtown;
      }

      console.log('Updated:', responseData.data)

      setTimeout(pollServer, 3000);
    });
  }

  pollServer();
});
