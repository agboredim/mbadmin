document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("paymentForm");

    form.addEventListener("submit", async function (event) {
        event.preventDefault(); // Prevent default form submission

        const formData = new FormData(form);
        const orderId = formData.get("o_id");
        const status = formData.get("status");
        const txRef = formData.get("tx_ref");
        const transactionId = formData.get("transaction_id");

        if (!orderId || !status || !txRef || !transactionId) {
            alert("❌ Missing required payment details!");
            return;
        }

        const requestData = { o_id: orderId, status, tx_ref: txRef, transaction_id: transactionId };

        try {
            const response = await fetch("/orders/confirm_payment/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestData)
            });

            let responseData;
            try {
                responseData = await response.json();
            } catch (error) {
                responseData = { error: "Invalid response from server" };
            }

            if (response.ok) {
                alert("✅ Payment Confirmed Successfully!");
            } else {
                alert(`❌ Payment Confirmation Failed: ${responseData.error || "Unknown error"}`);
            }
        } catch (error) {
            console.error("Error confirming payment:", error);
            alert("⚠️ Network error! Please try again.");
        }
    });
});
