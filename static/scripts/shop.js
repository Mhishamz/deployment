
$(document).ready(function() {
    $('#category-list li').click(function() {
        var category = $(this).data('category');
        
        // Highlight the selected category
        $('#category-list li').removeClass('active');
        $(this).addClass('active');

        // Fetch products based on the selected category
        $.ajax({
            url: '/filter_products',
            method: 'GET',
            data: { category: category },
            success: function(products) {
                // Clear the current product list
                $('#product-list').empty();
                
                // Populate the product list with the filtered products
                products.forEach(function(product) {
                    $('#product-list').append(
                        '<li data-category="' + product.category + '">' +
                            '<img src="' + product.image_url + '" alt="' + product.product_name + '">' +
                            '<h3>' + product.product_name + '</h3>' +
                            '<p>Subcategory: ' + product.sub_category + '</p>' +
                            '<p class="price">Price: Ksh ' + product.price + '</p>' +
                            '<p>Size: ' + product.size + '</p>' +
                            '<button onclick="addToCart(\'' + product.product_id + '\')">Add to Cart</button>' +
                        '</li>'
                    );
                });
            },
            error: function() {
                console.log('Error fetching products');
            }
        });
    });
});

// add to cart function
function addToCart(productId) {
    // Create an XMLHttpRequest object
    var xhr = new XMLHttpRequest();
  
    // Prepare the request URL
    var url = '/add_to_cart';
  
    // Prepare the request parameters
    var params = 'product_id=' + encodeURIComponent(productId);
  
    // Set up the request
    xhr.open('POST', url, true);
    xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
  
    // Define the callback function
    xhr.onload = function() {
      if (xhr.status === 200) {
        // Success: Update the cart dynamically
        var cartCount = document.getElementById('cart-count');
        var currentCount = parseInt(cartCount.innerText);
        cartCount.innerText = currentCount + 1;

        // Display success message

      } else {
        // Error: Display an error message
        alert('Error adding item to cart.');
      }
    };
  
    // Send the request
    xhr.send(params);
  }

function openProductPage(productId) {
      window.location.href = `/product/${productId}`;
  }