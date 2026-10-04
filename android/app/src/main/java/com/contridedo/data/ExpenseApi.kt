package com.contridedo.data

import com.google.gson.annotations.SerializedName
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.Path

/** Values serialized here intentionally match the web ExpenseCreatePayload contract. */
data class ExpenseCreatePayload(
    val description: String,
    @SerializedName("total_amount") val totalAmount: String,
    @SerializedName("payer_id") val payerId: Long,
    val splits: List<ExpenseSplitPayload>,
)

data class ExpenseSplitPayload(
    @SerializedName("user_id") val userId: Long,
    @SerializedName("amount_owed") val amountOwed: String,
    @SerializedName("calculation_method") val calculationMethod: String,
)

interface ExpenseApi {
    @POST("api/trips/{tripId}/expenses")
    suspend fun createExpense(
        @Path("tripId") tripId: Long,
        @Body payload: ExpenseCreatePayload,
    ): Response<ResponseBody>

    companion object {
        fun create(baseUrl: String): ExpenseApi = Retrofit.Builder()
            .baseUrl(baseUrl)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ExpenseApi::class.java)
    }
}
