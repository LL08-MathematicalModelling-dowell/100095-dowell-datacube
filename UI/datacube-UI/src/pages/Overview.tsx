/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../services/api';
import useAuthStore from '../store/authStore';
import toast from 'react-hot-toast';
import FilesSection from '../components/FileSection';
import AnalyticsCharts from '../components/AnalyticsCharts';
import { Card, PageHeader } from '../components/ui/Card';
import { QueryErrorBlock, RefreshButton } from '../components/ui/QueryRefresh';

// Define validation schema
const collectionFieldSchema = z.object({
  name: z.string().min(1, 'Field name is required'),
  type: z.string().min(1, 'Field type is required'),
});

const createDatabaseSchema = z.object({
  db_name: z.string().min(1, 'Database name is required').regex(/^[a-zA-Z0-9_-]+$/, 'Database name can only contain letters, numbers, underscores, and hyphens'),
  collections: z.array(
    z.object({
      name: z.string().min(1, 'Collection name is required'),
      fields: z.array(collectionFieldSchema).min(1, 'At least one field is required'),
    })
  ).min(1, 'At least one collection is required'),
});

type CreateDatabaseForm = z.infer<typeof createDatabaseSchema>;

interface Database {
  id: string;
  name: string;
}

const Overview = () => {
  const queryClient = useQueryClient();
  const { refreshToken } = useAuthStore();
  const [isFormOpen, setIsFormOpen] = useState(false);

  // Fetch databases and usage stats
  const {
    data: databases,
    isLoading,
    isError,
    isFetching,
    refetch,
  } = useQuery<Database[]>({
    queryKey: ['databases'],
    queryFn: async () => {
      const response = await api.get('/core/api/v1/dashboard/stats/');
      return response.databases;
    },
    enabled: !!refreshToken,
  });

  const isRefreshingDatabases = isFetching && !isLoading;

  // Create database mutation
  const createMutation = useMutation({
    mutationFn: (data: CreateDatabaseForm) => api.post('/api/v2/create_database/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['databases'] });
      setIsFormOpen(false);
      reset();
      toast.success('Database created successfully');
    },
    onError: (err) => {
      console.error('Failed to create database:', err);
      toast.error('Could not create database. Check the form and try again.');
    },
  });

  // Form setup
  const { register, control, handleSubmit, reset, formState: { errors } } = useForm<CreateDatabaseForm>({
    resolver: zodResolver(createDatabaseSchema),
    defaultValues: { db_name: '', collections: [{ name: '', fields: [{ name: '', type: '' }] }] },
  });

  const { fields: collections, append: appendCollection, remove: removeCollection } = useFieldArray({
    control,
    name: 'collections',
  });

  const onSubmit = (data: CreateDatabaseForm) => {
    createMutation.mutate(data);
  };

  return (
    <div className="max-w-6xl mx-auto pb-10">
      <PageHeader
        title="Overview"
        description="Databases, analytics, and file storage for your workspace."
      />

        <Card title="Analytics & performance" subtitle="Live usage from the observability API" className="mb-8">
          <AnalyticsCharts />
        </Card>

        <FilesSection />

        <Card
          title="Your databases"
          subtitle="Logical databases mapped to your MongoDB namespaces"
          className="mb-8"
          action={
            <div className="flex flex-wrap items-center gap-2">
              <RefreshButton
                onClick={() => refetch()}
                isRefreshing={isRefreshingDatabases}
                label="Reload"
              />
              <button
                onClick={() => setIsFormOpen(true)}
                className="rounded-[var(--radius-md)] bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-transform hover:brightness-110 active:scale-[0.98]"
                type="button"
              >
                Create database
              </button>
            </div>
          }
        >

          {isLoading && <p className="text-[var(--text-muted)]">Loading databases…</p>}
          {isError && (
            <QueryErrorBlock
              message="Could not load databases."
              onRetry={() => refetch()}
              isRefreshing={isRefreshingDatabases}
            />
          )}

          {!isLoading && !isError && databases && databases.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-[var(--surface-2)]/80">
                    <th className="p-3 text-left text-sm font-semibold text-[var(--text-primary)] rounded-tl-lg">Name</th>
                    <th className="p-3 text-left text-sm font-semibold text-[var(--text-primary)]">ID</th>
                    <th className="p-3 text-left text-sm font-semibold text-[var(--text-primary)] rounded-tr-lg">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {databases?.map((db) => (
                    <tr key={db.id} className="border-b border-[var(--border-subtle)] hover:bg-[var(--surface-0)] transition-colors">
                      <td className="p-3 font-medium text-[var(--text-primary)]">{db.name}</td>
                      <td className="p-3 font-[var(--font-mono)] text-sm text-[var(--text-muted)]">{db.id}</td>
                      <td className="p-3">
                        <Link
                          to={`/dashboard/database/${db.id}`}
                          className="font-medium text-[var(--accent-bright)] hover:underline transition-colors"
                        >
                          Open
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (!isLoading && !isError && databases?.length === 0) && (
            <div className="rounded-[var(--radius-md)] border border-dashed border-[var(--border)] bg-[var(--surface-0)] p-8 text-center">
              <p className="text-[var(--text-muted)] mb-4">No databases yet.</p>
              <button
                onClick={() => setIsFormOpen(true)}
                className="rounded-[var(--radius-md)] bg-[var(--accent)] px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:brightness-110"
              >
                Create your first database
              </button>
            </div>
          )}
        </Card>

        {/* Create Database Form Modal */}
        {isFormOpen && (
          <div className="fixed inset-0 bg-opacity-70 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-slate-800/90 p-6 sm:p-8 rounded-xl max-w-2xl w-full mx-auto border border-cyan-700 shadow-2xl relative">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white tracking-tight">
                  Create New Database
                </h2>
                <button
                  onClick={() => setIsFormOpen(false)}
                  className="text-slate-400 hover:text-white transition-colors text-2xl"
                  aria-label="Close form"
                >
                  &times;
                </button>
              </div>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div>
                  <label htmlFor="db_name" className="block text-sm font-medium text-slate-300 mb-2">
                    Database Name <span className="text-red-400">*</span>
                  </label>
                  <input
                    id="db_name"
                    {...register('db_name')}
                    placeholder="e.g., my_customer_project"
                    className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                    aria-invalid={errors.db_name ? 'true' : 'false'}
                  />
                  {errors.db_name && (
                    <p className="text-red-400 text-sm mt-1">{errors.db_name.message}</p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-slate-200 mb-3 flex items-center">
                    Collections & Fields <span className="text-red-400 ml-1">*</span>
                  </h3>
                  {errors.collections && (
                    <p className="text-red-400 text-sm mb-3">{errors.collections.message}</p>
                  )}
                  <div className="space-y-4">
                    {collections.map((collection, index) => (
                      <div key={collection.id} className="p-5 bg-slate-700/40 rounded-lg border border-slate-600/50 relative">
                        <input
                          {...register(`collections.${index}.name`)}
                          placeholder="Collection Name (e.g., 'users')"
                          className="w-full p-2 bg-slate-600/50 border border-slate-500 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors mb-3"
                          aria-invalid={errors.collections?.[index]?.name ? 'true' : 'false'}
                        />
                        {errors.collections?.[index]?.name && (
                          <p className="text-red-400 text-sm mb-3">{errors.collections[index].name?.message}</p>
                        )}

                        <h4 className="text-sm font-medium text-slate-300 mb-2">Fields for "{collection.name || 'New Collection'}" <span className="text-red-400">*</span></h4>
                        {errors.collections?.[index]?.fields && (
                          <p className="text-red-400 text-sm mb-3">{errors.collections[index].fields?.message}</p>
                        )}

                        <div className="space-y-2">
                          <CollectionFields fields={collection.fields} collectionIndex={index} control={control} register={register} errors={errors} />
                        </div>

                        <button
                          type="button"
                          onClick={() => removeCollection(index)}
                          className="absolute top-3 right-3 text-slate-400 hover:text-red-500 transition-colors"
                          aria-label="Remove collection"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
                        </button>
                      </div>
                    ))}
                  </div>
                  {errors.collections && (
                    <p className="text-red-400 text-sm mt-3">{errors.collections.message}</p>
                  )}
                  <button
                    type="button"
                    onClick={() => appendCollection({ name: '', fields: [{ name: '', type: '' }] })}
                    className="mt-4 text-cyan-500 hover:text-cyan-400 font-medium transition-colors flex items-center gap-1"
                    aria-label="Add another collection"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>
                    Add Another Collection
                  </button>
                </div>

                <div className="flex justify-end gap-4 mt-8 pt-6 border-t border-slate-700/60">
                  <button
                    type="button"
                    onClick={() => setIsFormOpen(false)}
                    className="bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white px-5 py-2.5 rounded-md text-sm font-medium transition-colors duration-200"
                    aria-label="Cancel"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-2.5 px-6 rounded-md text-sm transition-colors duration-200 shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="Create database"
                  >
                    {createMutation.isPending ? 'Creating...' : 'Create Database'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
    </div>
  );
};

export default Overview;

// Helper component for Collection Fields to manage nested field array
interface CollectionFieldsProps {
  fields: any[]; // Use correct type if available, e.g., Array<z.infer<typeof collectionFieldSchema>>
  collectionIndex: number;
  control: any;
  register: any;
  errors: any;
}

const CollectionFields: React.FC<CollectionFieldsProps> = ({ collectionIndex, control, register, errors }) => {
  const { fields: fieldArrayFields, append: appendField, remove: removeField } = useFieldArray({
    control,
    name: `collections.${collectionIndex}.fields`,
  });

  return (
    <div className="space-y-2">
      {fieldArrayFields.map((field, fieldIndex) => (
        <div key={field.id} className="flex gap-2 items-center">
          <input
            {...register(`collections.${collectionIndex}.fields.${fieldIndex}.name`)}
            placeholder="Field Name"
            className="flex-grow p-2 bg-slate-600/50 border border-slate-500 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
            aria-invalid={errors.collections?.[collectionIndex]?.fields?.[fieldIndex]?.name ? 'true' : 'false'}
          />
          <input
            {...register(`collections.${collectionIndex}.fields.${fieldIndex}.type`)}
            placeholder="Field Type (e.g., 'string', 'number')"
            className="flex-grow p-2 bg-slate-600/50 border border-slate-500 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
            aria-invalid={errors.collections?.[collectionIndex]?.fields?.[fieldIndex]?.type ? 'true' : 'false'}
          />
          <button
            type="button"
            onClick={() => removeField(fieldIndex)}
            className="text-slate-400 hover:text-red-500 transition-colors p-1"
            aria-label="Remove field"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
          </button>
        </div>
      ))}
      {errors.collections?.[collectionIndex]?.fields?._errors && (
        <p className="text-red-400 text-sm mt-1">{errors.collections[collectionIndex].fields._errors.join(', ')}</p>
      )}
      <button
        type="button"
        onClick={() => appendField({ name: '', type: '' })}
        className="mt-2 font-medium text-[var(--accent-bright)] transition-colors hover:opacity-90 flex items-center gap-1"
        aria-label="Add another field"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>
        Add Field
      </button>
    </div>
  );
};