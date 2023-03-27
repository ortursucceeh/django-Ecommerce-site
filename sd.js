    function GetCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie != '') {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();

          if (cookie.substring(0, name.length + 1) === (name + "=")){
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
      }
    }
    return cookieValue;
  }
    // Render the PayPal button into #paypal-button-container
    let amount = "{{ grand_total }}"
    let url = "{% url 'payments' %}"
    let csrf_token = GetCookie('csrf_token')
    let orderId = "{{order.order_number}}"
    let payment_method = "PayPal"
    
paypal.Buttons({
    style: {
        color: 'blue',
        shape: 'rect',
        label: 'pay',
        height: 40
    },

      createOrder: function(data, actions) {
          return actions.order.create({
            purchase_units: [{
              amount:{
                value: amount
              }
            }]
          });
        },

    onApprove: function (data, actions) {
        return actions.order.capture().then(function (details) {
            sendData();
              
            function sendData() {
                fetch(url, {
                    method: 'POST',
                    data: JSON.stringify(details),
                    headers: {
                        "Content-type": "application/json",
                        "X-CSRFToken": csrf_token
                    },
                    body: JSON.stringify({
                        orderID: orderId,
                        transID: details.id,
                        payment_method: payment_method,
                        status: details.status
                    }),
                }).then(response => response.json())
                    .then(data => console.log(data));
            }
        }
        )
    }
}).render('#paypal-button-container');