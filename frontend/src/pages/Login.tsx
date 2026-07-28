import { useState } from "react";
import "./Login.css";

const Login = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();

        console.log({
            email,
            password,
        });

        // TODO:
        // Call Django backend here
    };

    return (
        <div className="login-container">
            <div className="login-card">

                <h1>OV Quest</h1>
                <p className="subtitle">
                    Login to continue your journey
                </p>

                <form onSubmit={handleLogin}>

                    <div className="form-group">
                        <label>Email</label>

                        <input
                            type="email"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>

                        <input
                            type="password"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    <button type="submit">
                        Login
                    </button>

                </form>

                <div className="divider" />

                <p className="register">
                    Don't have an account?
                    <a href="#"> Register</a>
                </p>

            </div>
        </div>
    );
};

export default Login;