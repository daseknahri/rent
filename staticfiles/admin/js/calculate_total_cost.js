(function () {
    function init() {
        if (typeof django === "undefined" || typeof django.jQuery === "undefined") {
            console.log("Waiting for Django's jQuery...");
            setTimeout(init, 50);
            return;
        }

        var $ = django.jQuery;
        console.log("Django's jQuery is loaded successfully!");

        $(document).ready(function () {
            function fetchDailyRate(carId, callback) {
                if (!carId) return;

                $.ajax({
                    url: "/api/get-car-daily-rate/",
                    data: { car_id: carId },
                    dataType: "json",
                    success: function (response) {
                        if (response.daily_rate) {
                            var carDailyRate = parseFloat(response.daily_rate);
                            console.log("Car daily rate fetched:", carDailyRate);

                            // ✅ Set the actual daily rate (user can still change it manually)
                            if ($("#id_actual_daily_rate").val() === "") {
                                $("#id_actual_daily_rate").val(carDailyRate.toFixed(2));
                            }

                            if (callback) callback(); // Trigger total cost recalculation
                        }
                    },
                    error: function () {
                        console.error("Failed to fetch car's daily rate.");
                    }
                });
            }

            function updateTotalCost() {
                var startDate = $("#id_start_date").val();
                var endDate = $("#id_end_date").val();
                var actualDailyRate = parseFloat($("#id_actual_daily_rate").val()) || 0;
                var totalCostField = $("#id_total_cost");

                if (!startDate || !endDate || actualDailyRate === 0) {
                    console.warn("Incomplete data for calculation.");
                    totalCostField.val(""); // Clear if invalid
                    return;
                }

                var start = new Date(startDate);
                var end = new Date(endDate);

                if (isNaN(start.getTime()) || isNaN(end.getTime())) {
                    console.warn("Invalid date detected, skipping calculation...");
                    return;
                }

                var rentalDays = Math.max((end - start) / (1000 * 60 * 60 * 24), 1);
                var totalCost = rentalDays * actualDailyRate;

                console.log(`Total Cost: ${rentalDays} days × ${actualDailyRate} = ${totalCost}`);

                totalCostField.val(totalCost.toFixed(2)); // ✅ Set the total cost in the field

            }

            // ✅ Initial Fetch (if car is already selected)
            var selectedCarId = $("#id_car").val();
            if (selectedCarId) {
                console.log("Fetching daily rate for pre-selected car:", selectedCarId);
                fetchDailyRate(selectedCarId, updateTotalCost);
            }

            // ✅ Event Listeners
            $("#id_car").change(function () {
                var carId = $(this).val();
                fetchDailyRate(carId, updateTotalCost); // Fetch new daily rate and recalculate
            });

            $("#id_start_date, #id_end_date, #id_actual_daily_rate").on("change input blur", function () {
                updateTotalCost(); // Recalculate when dates or daily rate change
            });

            // Fix for Django Admin Date Picker
            $(document).on("click", ".ui-datepicker-close", function () {
                updateTotalCost();
            });
        });
    }

    init();
})();
