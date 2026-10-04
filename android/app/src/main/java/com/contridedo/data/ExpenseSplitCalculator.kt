package com.contridedo.data

import java.math.BigDecimal
import java.util.Locale

const val EQUAL_SPLIT = "equal"
const val PERCENTAGE_SPLIT = "percentage"
const val EXACT_SPLIT = "exact"

fun buildExpenseSplits(
    totalAmount: String,
    participantIds: List<Long>,
    calculationMethod: String,
    values: Map<Long, String> = emptyMap(),
): List<ExpenseSplitPayload> {
    require(participantIds.isNotEmpty()) { "Choose at least one participant." }
    require(participantIds.distinct().size == participantIds.size) { "Participants must be unique." }
    val totalCents = parseCents(totalAmount)
    require(totalCents > 0) { "Amount must be greater than zero." }

    val owedByUser = when (calculationMethod) {
        EQUAL_SPLIT -> {
            val base = totalCents / participantIds.size
            val remainder = totalCents % participantIds.size
            participantIds.mapIndexed { index, userId ->
                userId to (base + if (index < remainder) 1 else 0)
            }
        }
        EXACT_SPLIT -> {
            val splits = participantIds.map { userId ->
                userId to parseCents(values[userId].orEmpty())
            }
            require(splits.sumOf { it.second } == totalCents) {
                "Exact shares must add up to the total."
            }
            splits
        }
        PERCENTAGE_SPLIT -> {
            val percentages = participantIds.map { userId ->
                userId to parsePercentHundredths(values[userId].orEmpty())
            }
            require(percentages.sumOf { it.second } == 10_000L) {
                "Percentages must add up to 100%."
            }
            val baseShares = percentages.mapIndexed { index, (userId, percent) ->
                val product = totalCents * percent
                Triple(userId, product / 10_000L, product % 10_000L to index)
            }
            val remainingCents = totalCents - baseShares.sumOf { it.second }
            val bonusUsers = baseShares
                .sortedWith(compareByDescending<Triple<Long, Long, Pair<Long, Int>>> { it.third.first }
                    .thenBy { it.third.second })
                .take(remainingCents.toInt())
                .map { it.first }
                .toSet()
            baseShares.map { (userId, cents, _) ->
                userId to (cents + if (userId in bonusUsers) 1 else 0)
            }
        }
        else -> error("Unsupported calculation method.")
    }

    return owedByUser.map { (userId, cents) ->
        ExpenseSplitPayload(
            userId = userId,
            amountOwed = formatCents(cents),
            calculationMethod = calculationMethod,
        )
    }
}

private fun parseCents(value: String): Long {
    require(Regex("^\\d+(?:\\.\\d{1,2})?$").matches(value.trim())) {
        "Enter an amount with up to two decimal places."
    }
    return BigDecimal(value.trim()).movePointRight(2).longValueExact()
}

private fun parsePercentHundredths(value: String): Long {
    require(Regex("^\\d+(?:\\.\\d{1,2})?$").matches(value.trim())) {
        "Enter a valid percentage."
    }
    return BigDecimal(value.trim()).movePointRight(2).longValueExact()
        .also { require(it in 0..10_000) { "Percentages must be from 0 to 100." } }
}

private fun formatCents(cents: Long): String = String.format(
    Locale.US,
    "%d.%02d",
    cents / 100,
    cents % 100,
)
