import {useState, useEffect} from "react";
import Machines from "./components/Machines.jsx";
import Laundry from "./components/My-Laundry.jsx";
import Laundrystaff from "./components/Laundry-staff.jsx";

const API_URL = "http://127.0.0.1:8001";

export default function App() {
    const [machines, setMachines] = useState([]);
    const [selected, setSelected] = useState([null]);
    const [error, setError] = useState("");
    const [filtered, setFiltered] = useState(false);

    async function fetchMachines() {
        if (filtered) {
            const targetEndpoint = `${API_URL}/maachines?status = available`;
            const response = await fetch(targetEndpoint);
            if (!response.ok) throw new Error ("Failed to fectch machines");
            const data = await response.json();
            setMachines(data);
        }
    }

}

useEffect(() => {
    fetchMachines();

}, [filtered]);