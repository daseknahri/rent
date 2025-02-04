(function() {
    function init() {
        if (typeof django === "undefined" || typeof django.jQuery === "undefined") {
            console.log("Waiting for Django's jQuery...");
            setTimeout(init, 50);
            return;
        }

        var $ = django.jQuery;  // ✅ Use Django's jQuery
        console.log("Django's jQuery is loaded successfully!");

        $(document).ready(function() {
            var dailyRate = 0;

            function updateTotalCost() {
                var startDate = $("#id_start_date").val();
                var endDate = $("#id_end_date").val();
                var totalCostField = $("#id_total_cost");  // ✅ Now it will be found
                console.log(startDate, endDate, totalCostField)
                if (startDate && endDate && dailyRate > 0) {
                    var start = new Date(startDate);
                    var end = new Date(endDate);
                    var rentalDays = Math.max((end - start) / (1000 * 60 * 60 * 24), 1);
                    var totalCost = rentalDays * dailyRate;
                    totalCostField.text(totalCost.toFixed(2));  // ✅ Update the read-only field
                }
            }
            // 🔥 Listen for both manual input and calendar selection
            $("#id_start_date, #id_end_date").on("change input blur", updateTotalCost);

            // 🔥 Fix for Django Admin's Date Picker
            $(document).on("click", ".ui-datepicker-close", function() {
                updateTotalCost();
            });
            $("#id_car").change(function() {
                var carId = $(this).val();
                if (!carId) return;
                $.ajax({
                    url: "/api/get-car-daily-rate/",
                    data: { car_id: carId },
                    dataType: "json",
                    success: function(response) {
                        if (response.daily_rate) {
                            dailyRate = parseFloat(response.daily_rate);
                            updateTotalCost();
                        }
                    }
                });
            });  
        });
    }

    init();
})();
