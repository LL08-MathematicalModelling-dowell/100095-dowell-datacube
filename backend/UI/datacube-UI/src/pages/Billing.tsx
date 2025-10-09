// import { useQuery } from '@tanstack/react-query';
// import api from '../services/api.ts'; // Still import api, but we won't actually call it for now.

// Add a type for the billing data to ensure type safety
interface BillingData {
  plan: string;
  renewDate: string; // Assuming this is a string, could be Date if parsed
  stripePortal: string;
}

const DUMMY_BILLING_DATA: BillingData = {
  plan: 'Pro Plan',
  renewDate: '2024-12-31',
  stripePortal: '#',
};

const Billing = () => {
  const data: BillingData = DUMMY_BILLING_DATA;
  const isLoading: boolean = false;
  const error: boolean = false;

  // If you want to simulate a loading state (e.g., for 2 seconds):
  // const [mockLoading, setMockLoading] = useState(true);
  // useEffect(() => {
  //   const timer = setTimeout(() => setMockLoading(false), 2000); // Simulate 2s loading
  //   return () => clearTimeout(timer);
  // }, []);
  // const data = mockLoading ? undefined : DUMMY_BILLING_DATA;
  // const isLoading = mockLoading;
  // const error = false;


  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900 text-slate-300 font-sans">
        <p className="text-xl text-slate-400">Loading billing information...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900 text-red-400 font-sans">
        <p className="text-xl">Error loading billing information. Please try again later.</p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-slate-300 font-sans min-h-screen p-6 sm:p-10">
      <div className="max-w-3xl mx-auto py-12">
        <h1 className="text-5xl font-extrabold text-white tracking-tight mb-8 text-center bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-teal-500">
          Billing & Subscription
        </h1>
        <p className="text-lg text-slate-400 mb-10 text-center max-w-2xl mx-auto">
          Manage your DataCube plan and access your billing history securely.
        </p>

        {/* Development Notice */}
        <div className="bg-amber-900/40 border border-amber-800/60 text-amber-300 p-4 rounded-lg mb-8 text-center flex items-center justify-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" x2="12" y1="9" y2="13" /><line x1="12" x2="12.01" y1="17" y2="17" /></svg>
          <p className="font-semibold">This page is currently under development. Displaying dummy data.</p>
        </div>

        <div className="bg-slate-800/60 rounded-xl shadow-2xl border border-slate-700/80 p-8 mb-8 relative overflow-hidden">
          {/* Decorative background element */}
          <div className="absolute -top-10 -right-10 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl opacity-50"></div>
          <div className="absolute -bottom-10 -left-10 w-48 h-48 bg-teal-500/10 rounded-full blur-3xl opacity-50"></div>

          <h2 className="text-3xl font-bold text-white mb-6 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-cyan-400 mr-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M17 5H7l5 5-5 5H17M19 18H5" /></svg>
            Your Current Plan
          </h2>

          <div className="space-y-4 text-lg">
            <p className="flex items-center">
              <span className="font-semibold text-slate-200 w-32">Plan:</span>
              <span className="text-cyan-400 font-medium">{data?.plan || 'N/A'}</span>
            </p>
            <p className="flex items-center">
              <span className="font-semibold text-slate-200 w-32">Renews On:</span>
              <span className="text-slate-300">{data?.renewDate || 'N/A'}</span>
            </p>
          </div>

          <div className="mt-10 pt-6 border-t border-slate-700/60 flex flex-col sm:flex-row items-center justify-between gap-6">
            <p className="text-slate-400 text-base max-w-sm">
              Access your detailed billing history, change payment methods, or update your subscription plan.
            </p>
            <a
              href={data?.stripePortal}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-3 px-8 rounded-md transition-colors duration-200 text-lg shadow-lg hover:shadow-xl group"
            >
              Open Billing Portal
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2 -mr-1 group-hover:translate-x-1 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 7h10v10M7 17L17 7" /></svg>
            </a>
          </div>
        </div>

        {/* Optional: Add a section for recent invoices or plan details */}
        <div className="mt-12 text-center text-slate-500 text-sm">
          Having trouble? Contact support for assistance.
        </div>

      </div>
    </div>
  );
};

export default Billing;



// import { useQuery } from '@tanstack/react-query';
// import api from '../services/api.ts';

// // Add a type for the billing data to ensure type safety
// interface BillingData {
//   plan: string;
//   renewDate: string; // Assuming this is a string, could be Date if parsed
//   stripePortal: string;
// }

// const Billing = () => {
//   const { data, isLoading, error } = useQuery<BillingData>({
//     queryKey: ['billing'],
//     queryFn: async () => {
//       const response = await api.get('/billing');
//       // Assuming the API response directly matches BillingData
//       return response;
//     }
//   });

//   if (isLoading) {
//     return (
//       <div className="flex items-center justify-center min-h-screen bg-slate-900 text-slate-300 font-sans">
//         <p className="text-xl text-slate-400">Loading billing information...</p>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="flex items-center justify-center min-h-screen bg-slate-900 text-red-400 font-sans">
//         <p className="text-xl">Error loading billing information. Please try again later.</p>
//       </div>
//     );
//   }

//   return (
//     <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-slate-300 font-sans min-h-screen p-6 sm:p-10">
//       <div className="max-w-3xl mx-auto py-12">
//         <h1 className="text-5xl font-extrabold text-white tracking-tight mb-8 text-center bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-teal-500">
//           Billing & Subscription
//         </h1>
//         <p className="text-lg text-slate-400 mb-10 text-center max-w-2xl mx-auto">
//           Manage your DataCube plan and access your billing history securely.
//         </p>

//         <div className="bg-slate-800/60 rounded-xl shadow-2xl border border-slate-700/80 p-8 mb-8 relative overflow-hidden">
//           {/* Decorative background element */}
//           <div className="absolute -top-10 -right-10 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl opacity-50"></div>
//           <div className="absolute -bottom-10 -left-10 w-48 h-48 bg-teal-500/10 rounded-full blur-3xl opacity-50"></div>

//           <h2 className="text-3xl font-bold text-white mb-6 flex items-center">
//             <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-cyan-400 mr-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M17 5H7l5 5-5 5H17M19 18H5" /></svg>
//             Your Current Plan
//           </h2>

//           <div className="space-y-4 text-lg">
//             <p className="flex items-center">
//               <span className="font-semibold text-slate-200 w-32">Plan:</span>
//               <span className="text-cyan-400 font-medium">{data?.plan || 'N/A'}</span>
//             </p>
//             <p className="flex items-center">
//               <span className="font-semibold text-slate-200 w-32">Renews On:</span>
//               <span className="text-slate-300">{data?.renewDate || 'N/A'}</span>
//             </p>
//           </div>

//           <div className="mt-10 pt-6 border-t border-slate-700/60 flex flex-col sm:flex-row items-center justify-between gap-6">
//             <p className="text-slate-400 text-base max-w-sm">
//               Access your detailed billing history, change payment methods, or update your subscription plan.
//             </p>
//             <a
//               href={data?.stripePortal}
//               target="_blank"
//               rel="noopener noreferrer"
//               className="inline-flex items-center bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-3 px-8 rounded-md transition-colors duration-200 text-lg shadow-lg hover:shadow-xl group"
//             >
//               Open Billing Portal
//               <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2 -mr-1 group-hover:translate-x-1 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 7h10v10M7 17L17 7" /></svg>
//             </a>
//           </div>
//         </div>

//         {/* Optional: Add a section for recent invoices or plan details */}
//         <div className="mt-12 text-center text-slate-500 text-sm">
//           Having trouble? Contact support for assistance.
//         </div>

//       </div>
//     </div>
//   );
// };

// export default Billing;