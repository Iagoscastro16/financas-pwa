import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { useEnterToNextField } from "../hooks/useEnterToNextField";
import "./Login.css";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const { ref: formRef, onKeyDown: handleFormKeyDown } = useEnterToNextField();

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate("/dashboard", { replace: true });
    } catch {
      setError("Usuário ou senha inválidos.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login">
      <form
        className="login__form"
        onSubmit={handleSubmit}
        ref={formRef}
        onKeyDown={handleFormKeyDown}
      >
        <h1 className="login__title">Finanças</h1>

        <label className="login__label" htmlFor="username">
          Usuário
        </label>
        <input
          id="username"
          className="login__input"
          type="text"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          required
        />

        <label className="login__label" htmlFor="password">
          Senha
        </label>
        <input
          id="password"
          className="login__input"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        {error && <p className="login__error">{error}</p>}

        <button className="login__button" type="submit" disabled={loading}>
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
