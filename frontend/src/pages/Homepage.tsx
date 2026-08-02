import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./HomePage.css";


const HomePage = () => {

    const { user, isGuest, logout } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (!user && !isGuest) {
            navigate("/login");
        }
    }, [user, isGuest, navigate]);

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    if (!user && !isGuest) {
        return null;
    }

    return (

        <div className="home-container">

            <div className="home-card">

                <h1>
                    {
                        isGuest
                        ? "Welcome, traveler 🚆"
                        : `Welcome, ${user?.username} 🚆`
                    }
                </h1>

                <p>
                    {
                        isGuest
                        ? "Explore public transport without an account"
                        : "Ready for your next journey?"
                    }
                </p>

                <div className="stats">
                    <div className="stat-box">

                        <h2>
                            Level 1
                        </h2>

                        <p>
                            Explorer
                        </p>

                    </div>

                    <div className="stat-box">

                        <h2>
                            0 XP
                        </h2>

                        <p>
                            Total experience
                        </p>

                    </div>
                </div>

                {
                    !isGuest && (
                        <button onClick={handleLogout}>
                            Logout
                        </button>
                    )
                }

                {
                    isGuest && !user && (
                        <button onClick={() => {
                            navigate("/login");
                        }}>
                            Back to Login
                        </button>
                    )
                }

            </div>
        </div>

    );
};
export default HomePage;