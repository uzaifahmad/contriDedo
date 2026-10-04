package com.contridedo.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import com.google.gson.Gson
import com.google.gson.JsonParser

class ExpenseSplitCalculatorTest {
    @Test
    fun equalSplitAssignsRemainderCentsDeterministically() {
        val splits = buildExpenseSplits("10.00", listOf(101L, 102L, 103L), EQUAL_SPLIT)

        assertEquals(listOf("3.34", "3.33", "3.33"), splits.map { it.amountOwed })
        assertEquals(listOf(101L, 102L, 103L), splits.map { it.userId })
        assertEquals(setOf(EQUAL_SPLIT), splits.map { it.calculationMethod }.toSet())
    }

    @Test
    fun percentageSplitAmountsAddUpExactly() {
        val splits = buildExpenseSplits(
            totalAmount = "10.00",
            participantIds = listOf(101L, 102L, 103L),
            calculationMethod = PERCENTAGE_SPLIT,
            values = mapOf(101L to "33.34", 102L to "33.33", 103L to "33.33"),
        )

        assertEquals(listOf("3.34", "3.33", "3.33"), splits.map { it.amountOwed })
    }

    @Test
    fun requestSerializesTheSharedWebApiContract() {
        val request = ExpenseCreatePayload(
            description = "Cabin snacks",
            totalAmount = "10.00",
            payerId = 101L,
            splits = listOf(ExpenseSplitPayload(101L, "10.00", EQUAL_SPLIT)),
        )
        val body = JsonParser.parseString(Gson().toJson(request)).asJsonObject
        val split = body.getAsJsonArray("splits").single().asJsonObject

        assertEquals(setOf("description", "total_amount", "payer_id", "splits"), body.keySet())
        assertEquals("10.00", body.get("total_amount").asString)
        assertEquals(101L, body.get("payer_id").asLong)
        assertFalse(body.has("trip_id"))
        assertEquals(setOf("user_id", "amount_owed", "calculation_method"), split.keySet())
        assertTrue(body.get("splits").asJsonArray.size() == 1)
    }
}
