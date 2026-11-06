const { onCall, onRequest } = require("firebase-functions/v2/https");
const { initializeApp } = require("firebase-admin/app");
const { getAppCheck } = require("firebase-admin/app-check");
const { getAuth } = require("firebase-admin/auth");

initializeApp();

const ALLOWED_APP_ID = "1:59012385614:android:b679cde719174f35acec1f";

exports.mintAppCheckToken = onRequest(async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).json({ error: true, reason: "Method not allowed." });
    return;
  }

  const authHeader = req.get("authorization") || "";
  const match = authHeader.match(/^Bearer (.+)$/);
  if (!match) {
    res.status(401).json({ error: true, reason: "Missing Authorization bearer token." });
    return;
  }

  const idToken = match[1];
  try {
    await getAuth().verifyIdToken(idToken);
  } catch (err) {
    res.status(401).json({ error: true, reason: "Invalid auth token." });
    return;
  }

  const appId = req.body?.appId;
  if (appId !== ALLOWED_APP_ID) {
    res.status(403).json({ error: true, reason: "App ID not allowed." });
    return;
  }

  try {
    const appCheckToken = await getAppCheck().createToken(appId);
    res.status(200).json({
      token: appCheckToken.token,
      ttlMillis: appCheckToken.ttlMillis
    });
  } catch (err) {
    console.error("mintAppCheckToken createToken failed", err);
    const message = err?.message || String(err);
    res.status(500).json({ error: true, reason: message });
  }
});

exports.validateScanPayload = onCall(
  {
    enforceAppCheck: true
  },
  (request) => {
    if (!request.app) {
      return {
        success: false,
        error: true,
        reason: "App Check token is required."
      };
    }

    if (!request.auth) {
      return {
        success: false,
        error: true,
        reason: "Authentication required."
      };
    }

    const rawValue = request.data?.value;
    if (typeof rawValue !== "string") {
      return {
        success: false,
        error: true,
        reason: "Expected 'value' to be a string."
      };
    }

    const parts = rawValue.split("+");
    if (parts.length !== 3) {
      return {
        success: false,
        error: true,
        reason: "Expected three '+'-separated parts."
      };
    }

    const [uidPart, numberPart, timestampPart] = parts;
    if (uidPart !== request.auth.uid) {
      return {
        success: false,
        error: true,
        reason: "First part: Should be a UID for the current user."
      };
    }

    const numericValue = Number(numberPart);
    if (!Number.isFinite(numericValue)) {
      return {
        success: false,
        error: true,
        reason: "Second part: Must be a number."
      };
    }

    if (numericValue < 100) {
      return {
        success: false,
        error: true,
        reason: "Second part: Purchase must be 100 or above."
      };
    }

    const nowSeconds = Math.floor(Date.now() / 1000);
    let timestampSeconds = Number(timestampPart);
    if (!Number.isFinite(timestampSeconds)) {
      return {
        success: false,
        error: true,
        reason: "Third part: Must be a unix timestamp."
      };
    }

    if (timestampSeconds > 1_000_000_000_000) {
      timestampSeconds = Math.floor(timestampSeconds / 1000);
    }

    const thirtyDaysSeconds = 30 * 24 * 60 * 60;
    if (timestampSeconds > nowSeconds || timestampSeconds < nowSeconds - thirtyDaysSeconds) {
      return {
        success: false,
        error: true,
        reason: "Third part: Purchase must be within the last 30 days."
      };
    }

    return {
      success: true,
      reward: "CTF{Dr0pTh3Beat5andBar5}"
    };
  }
);
