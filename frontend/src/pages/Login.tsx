import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Login.css";


const Login = () => {

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(false);
    const { login, continueAsGuest } = useAuth();
    const navigate = useNavigate();
    const handleLogin = (e: React.FormEvent) => {

        e.preventDefault();
        setError(false);
        const success = login(
            username,
            password
        );
        if (!success) {

            setError(true);

            return;

        }
        navigate("/home");
    };

    return (

        <div className="login-container">

            <div className="login-card">

                <h1>
                    OV Quest
                </h1>

                <p className="subtitle">
                    Login to continue your journey
                </p>

                <form onSubmit={handleLogin}>

                    <div className="form-group">

                        <label>
                            Username
                        </label>

                        <input

                            className={
                                error
                                    ? "input-error"
                                    : ""
                            }

                            type="text"
                            placeholder="Enter username"
                            value={username}
                            onChange={(e) => {
                                setUsername(e.target.value);
                                setError(false);
                            }}
                            required
                        />

                    </div>

                    <div className="form-group">

                        <label>
                            Password
                        </label>

                        <input
                            className={
                                error
                                    ? "input-error"
                                    : ""
                            }
                            type="password"
                            placeholder="Enter password"
                            value={password}
                            onChange={(e) => {
                                setPassword(e.target.value);
                                setError(false);
                            }}
                            required
                        />

                    </div>

                    {
                        error && (
                            <p className="error-message">
                                username and password combination does not exist
                            </p>
                        )
                    }

                    <button type="submit">
                        Login
                    </button>


                    <button
                        type="button"
                        className="guest-button"
                        onClick={() => {
                            continueAsGuest();
                            navigate("/home");
                        }}
                    >
                        Continue without logging in
                    </button>

                </form>

                <div className="divider" />

                <p className="register">
                    Don't have an account?
                    <Link to="/register">
                        Register
                    </Link>
                </p>

            </div>
        </div>

    );

};
export default Login;