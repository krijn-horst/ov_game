import { useAuth } from "../context/AuthContext";
import "./Homepage.css";


const HomePage = () => {

    const { user, isGuest} = useAuth();

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

            </div>
        </div>

    );
};
export default HomePage;