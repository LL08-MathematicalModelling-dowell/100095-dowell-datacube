import { Route, Routes } from "react-router-dom";
import Healthcheck from "./Pages/SeverStatus/ServerHealthCheck";

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<Healthcheck />} />
    </Routes>
  ) 
};

export default App;
