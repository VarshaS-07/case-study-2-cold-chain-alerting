
import { useState } from "react";
import { LockKeyhole, Mail, ShieldCheck } from "lucide-react";
import { api, saveToken } from "./api";
import "./Login.css";

export default function Login({ onSuccess }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState("password");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (step === "password") {
        await api.login(username, password);
        setPassword("");
        setStep("otp");
      } else {
        const result = await api.verifyOTP(username, otp);
        saveToken(result.access_token);
        onSuccess();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <ShieldCheck size={30} />
        </div>

        <h1>Nimbus Freight</h1>
        <p className="login-subtitle">
          Secure Cold-Chain Operations Portal
        </p>

        <h2>
          {step === "password"
            ? "Administrator Login"
            : "Verify Your Identity"}
        </h2>

        <p className="login-description">
          {step === "password"
            ? "Enter your administrator credentials."
            : "Enter the six-digit code sent to your registered email."}
        </p>

        <form onSubmit={handleSubmit}>
          {step === "password" ? (
            <>
              <label>Username</label>
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />

              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </>
          ) : (
            <>
              <label>Email Verification Code</label>
              <div className="otp-label">
                <Mail size={16} />
                Code expires in 5 minutes
              </div>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                value={otp}
                onChange={(e) =>
                  setOtp(e.target.value.replace(/\D/g, ""))
                }
                placeholder="000000"
                className="otp-input"
                autoComplete="one-time-code"
                required
              />
            </>
          )}

          {error && <div className="login-error">{error}</div>}

          <button type="submit" disabled={loading}>
            <LockKeyhole size={17} />
            {loading
              ? "Please wait..."
              : step === "password"
                ? "Continue Securely"
                : "Verify & Sign In"}
          </button>
        </form>

        {step === "otp" && (
          <button
            type="button"
            className="back-button"
            onClick={() => {
              setStep("password");
              setOtp("");
              setError("");
            }}
          >
            Back to login
          </button>
        )}

        <div className="login-footer">
          Authorized personnel only · Nimbus Freight
        </div>
      </div>
    </div>
  );
}
