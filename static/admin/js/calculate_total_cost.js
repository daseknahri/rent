(function() {
    function init() {
        if (typeof django === "undefined" || typeof django.jQuery === "undefined") {
            console.log("Waiting for Django's jQuery...");
            setTimeout(init, 50);
            return;
        }

        var $ = django.jQuery;
        console.log("Django's jQuery is loaded successfully!");

        $(document).ready(function() {
            var dailyRate = 0;

            function fetchDailyRate(carId, callback) {
                if (!carId) return;
                
                $.ajax({
                    url: "/api/get-car-daily-rate/",
                    data: { car_id: carId },
                    dataType: "json",
                    success: function(response) {
                        if (response.daily_rate) {
                            dailyRate = parseFloat(response.daily_rate);
                            console.log("Car daily rate updated:", dailyRate);
                            if (callback) callback();  // ✅ Call update function after getting the rate
                        }
                    },
                    error: function() {
                        console.error("Failed to fetch daily rate.");
                    }
                });
            }

            function updateTotalCost(forceRecalculate = false) {
                var startDate = $("#id_start_date").val();
                var endDate = $("#id_end_date").val();
                var totalCostField = $("#id_total_cost");

                console.log("Updating Total Cost:", startDate, endDate, "Daily Rate:", dailyRate);

                if (!startDate || !endDate) {
                    console.warn("Skipping calculation: missing start or end date.");
                    return;
                }

                var start = new Date(startDate);
                var end = new Date(endDate);

                if (isNaN(start.getTime()) || isNaN(end.getTime())) {
                    console.warn("Invalid date detected, skipping calculation...");
                    return;
                }

                var rentalDays = Math.max((end - start) / (1000 * 60 * 60 * 24), 1);

                // 🔥 If dailyRate is still 0, force a recalculation after fetching it
                if (dailyRate === 0 && !forceRecalculate) {
                    console.warn("Daily rate is 0, fetching again...");
                    var carId = $("#id_car").val();
                    fetchDailyRate(carId, updateTotalCost);  // ✅ Fetch rate and recalculate after
                    return;
                }

                var totalCost = rentalDays * dailyRate;
                totalCostField.text(totalCost.toFixed(2));
            }

            // 🔥 Fetch daily rate on page load if a car is already selected
            var selectedCarId = $("#id_car").val();
            if (selectedCarId) {
                console.log("Fetching daily rate for pre-selected car:", selectedCarId);
                fetchDailyRate(selectedCarId, updateTotalCost);
            }

            // 🔥 Listen for date changes and force recalculation
            $("#id_start_date, #id_end_date").on("change input blur", function() {
                updateTotalCost(true);
            });

            // 🔥 Fix for Django Admin's Date Picker
            $(document).on("click", ".ui-datepicker-close", function() {
                updateTotalCost(true);
            });

            $("#id_car").change(function() {
                var carId = $(this).val();
                fetchDailyRate(carId, updateTotalCost);  // ✅ Ensure rate is fetched on car change
            });

        });
    }

    init();
})();
